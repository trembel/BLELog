"""
blelog/ActiveConnection.py
A single connection to a specific device. Managed by ConnectionMgr.

BLELog - Philipp Schilk, 2022
PBL, ETH Zuerich
---------------------------------
"""
import asyncio
import enum
import functools
import logging
import time
from asyncio import Event
from asyncio.queues import Queue, QueueFull
from enum import Enum
from typing import Dict, Union

from bleak import BleakClient
from bleak.exc import BleakDBusError, BleakError

from blelog.Configuration import Characteristic, Configuration
from blelog.ConsumerMgr import NotifData


@enum.unique
class ConnectionState(Enum):
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2

    def __str__(self):
        return super().__str__().split('.')[1]


class ActiveConnectionException(Exception):
    pass


class ActiveConnection:
    def __init__(self, adr: str, name: str, config: Configuration, output: Queue) -> None:
        self.adr = adr
        self.name = name
        self.config = config
        self.state = ConnectionState.CONNECTING
        self.disconnected_callback_flag = False
        self.did_disconnect = False

        self.output = output

        self.con = None  # type: Union[BleakClient, None]

        self.initial_connection_time = None
        self.last_notif = {c.uuid: None for c in config.characteristics}  # type: Dict[str, Union[None, int]]

        self.log = logging.getLogger('log')

    async def run(self, halt: Event) -> None:
        log = logging.getLogger('log')
        try:
            con = BleakClient(
                self.adr,
                timeout=self.config.connection_timeout_scan
            )
            con.set_disconnected_callback(self._disconnected_callback)

            self.con = con

            try:
                # Ensure there was no disconnect before this connection got a chance to run:
                if self.did_disconnect:
                    raise ActiveConnectionException()

                # Connect:
                await self._connect(self.con)
                self.initial_connection_time = time.monotonic_ns()

                # Start zephyr fix task, if the zephyr hotfix is enabled:
                if self.config.zephyr_fix_enabled:
                    self.fix_task = asyncio.create_task(self._task_zephyr_fix(halt, con))
                    asyncio.create_task(self._task_zephyr_fix(halt, con))

                while not halt.is_set():
                    # Check for disconnection
                    # (Flag set by disconnect callback or when this connection is manually disconnected)
                    if self.did_disconnect:
                        log.warning('Connection to %s lost!' % self.name)
                        raise ActiveConnectionException()

                    await self._check_for_timeout()

                    await asyncio.sleep(0.02)

            except ActiveConnectionException:
                pass
            finally:
                await self._do_disconnect()

            self.state = ConnectionState.DISCONNECTED

        except Exception as e:
            log.error('Connection %s encountered an exception: %s' % (self.name, str(e)))
            log.exception(e)
            self.did_disconnect = True
        finally:
            if halt.is_set():
                print('Connection %s shut down...' % self.name)

    async def _connect(self, con: BleakClient) -> None:
        log = logging.getLogger('log')

        # Note: According to the docks, bleak generates exceptions if connecting fails under linux,
        # while only returning false on other platforms.
        # This should handle all cases.
        try:
            ok = await asyncio.wait_for(con.connect(), self.config.connection_timeout_hard)
            if not ok:
                log.warning('Failed to connect to %s!' % self.name)
                raise ActiveConnectionException()
        except BleakDBusError as e:
            log.warning('Failed to connect to %s: DBus Error.' % self.name)
            log.exception(e)
            raise ActiveConnectionException()
        except BleakError as e:
            log.warning('Failed to connect to %s: %s' % (self.name, e))
            log.exception(e)
            raise ActiveConnectionException()
        except asyncio.TimeoutError:
            log.warning('Failed to connect to %s: Timeout' % self.name)
            raise ActiveConnectionException()
        except OSError as e:
            log.warning('Failed to connect to %s: OSError' % self.name)
            log.exception(e)
            raise ActiveConnectionException()

        log.info('Established connection to %s!' % self.name)

        # Enable notifications for all characteristics:
        for char in self.config.characteristics:
            # Generate a wrapper around the callback function to pass characteristic along.
            # Bleak does not seem to offer a documented interface on how the 'dev' int
            # passed to the callback can be used to identify which characteristic caused the
            # notification
            callback_wrapper = functools.partial(self._notif_callback, char=char)
            await con.start_notify(char.uuid, callback_wrapper)

        log.info('Enabled notifications for all characteristic for %s!' % self.name)
        self.state = ConnectionState.CONNECTED

    async def _check_for_timeout(self) -> None:
        log = logging.getLogger('log')

        for char in self.config.characteristics:
            if char.timeout is not None:
                last_notif = self.last_notif[char.uuid]

                if last_notif is not None:
                    # Check if normal timeout expired
                    timeout = char.timeout
                    has_been = (time.monotonic_ns() - last_notif)/1e9

                    if has_been > timeout:
                        log.warning('%s: Timeout for characteristic %s expired, disconnecting..' %
                                    (self.name, char.name))
                        await self._do_disconnect()
                        raise ActiveConnectionException()

                elif self.config.initial_characteristic_timeout is not None:
                    if self.initial_connection_time is None:
                        raise Exception("Implementation error")

                    # Check if initial timeout expired
                    timeout = char.timeout + self.config.initial_characteristic_timeout
                    has_been = (time.monotonic_ns() - self.initial_connection_time) / 1e9

                    if has_been > timeout:
                        log.warning('%s: Never received a notification for %s, disconnecting...' %
                                    (self.name, char.name))
                        await self._do_disconnect()

    def _disconnected_callback(self, _) -> None:
        self.did_disconnect = True

    def _notif_callback(self, dev: int, data: bytearray, char: Characteristic) -> None:
        _ = dev

        self.last_notif[char.uuid] = time.monotonic_ns()

        # Decode and package data:
        try:
            decoded_data = char.data_decoder(data)
            result = NotifData(self.adr, self.name, char, decoded_data)
            try:
                self.output.put_nowait(result)
            except QueueFull:
                self.log.error("%s failed to put data into queue!" % self.name)
        except Exception as e:
            self.log.error("Decoder for %s raised an exception: %s" % (char.name, str(e)))
            self.log.exception(e)

    async def _do_disconnect(self) -> None:
        log = logging.getLogger('log')
        if self.con is not None:
            try:
                did_disconnect = await asyncio.wait_for(self.con.disconnect(), timeout=20)
                if did_disconnect:
                    log.warning('Disconnected from %s.' % self.name)
                else:
                    log.warning('Failed to disconnect from %s: Bleak Error.' % self.name)
            except BleakDBusError:
                log.warning('Failed to disconnect from %s: DBus Error.' % self.name)
            except BleakError as e:
                log.warning('Failed to disconnect from %s: %s' % (self.name, e))
            except asyncio.TimeoutError:
                log.warning('Failed to disconnect from %s: Timeout' % self.name)
            except OSError:
                log.warning('Failed to disconnect from %s: OSError' % self.name)
            finally:
                self.did_disconnect = True

    async def _task_zephyr_fix(self, halt: Event, con: BleakClient) -> None:
        """ Repeadetly poll a set characteristic to work around a zephyr bug"""

        logged_enabled = False

        try:
            while not halt.is_set():
                last_heartbeat = time.monotonic()
                _ = await asyncio.wait_for(con.read_gatt_char(self.config.zephyr_fix_heartbeat_characterisitc_uuid),
                                           timeout=self.config.zephyr_fix_heartbeat_timeout)

                if not logged_enabled:
                    logged_enabled = True
                    self.log.info("%s: Zephyr fix running." % self.name)

                time_waited = time.monotonic() - last_heartbeat

                if(time_waited < self.config.zephyr_fix_heartbeat_poll_rate):
                    to_wait = min(self.config.zephyr_fix_heartbeat_poll_rate - time_waited, 0)
                    await asyncio.sleep(to_wait)

        except asyncio.TimeoutError:
            # Manual read took longer than timeout.
            self.log.warning("%s's zephyr-fix read timed-out. Disconnecting.." % self.name)
            await self._do_disconnect()
        except (BleakDBusError, BleakError, OSError) as e:
            self.log.warning('%s: Failed to read zephyr-fix characteristic. (%s)' % (self.name, e))
            await self._do_disconnect()
        except Exception as e:
            self.log.error('Connection %s\' zephyr-fix encountered an exception: %s' % (self.name, str(e)))
            self.log.exception(e)
            self.did_disconnect = True

    def active_time_str(self) -> str:
        if self.initial_connection_time is None:
            return "xx:xx:xx"
        else:
            active_s = (time.monotonic_ns() - self.initial_connection_time) / 1e9
            h = active_s // (3600)
            active_s %= (3600)
            min = active_s // 60
            active_s %= 60
            s = active_s // 1
            return "%02i:%02i:%02i" % (h, min, s)
