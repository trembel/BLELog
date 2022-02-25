from asyncio.queues import Queue, QueueFull
import functools
import time
from typing import Union, Dict
import asyncio
from asyncio import Event
import enum
from enum import Enum
import logging

from bleak import BleakClient
from bleak.exc import BleakDBusError, BleakError

from blelog.Configuration import Characteristic, Configuration
from blelog.consumers.ConsumerMgr import NotifData


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

                while not halt.is_set():
                    # Check for disconnection
                    # (Flag set by disconnect callback or when this connection is manully disconnected)
                    if self.did_disconnect:
                        log.warning('Connection to %s lost!' % self.name)
                        raise ActiveConnectionException()

                    await self._check_for_timeout(con)

                    await asyncio.sleep(0.02)

            except ActiveConnectionException:
                pass
            finally:
                if self.con is not None:
                    if self.con.is_connected:
                        await self.con.disconnect()

            self.state = ConnectionState.DISCONNECTED

        except Exception as e:
            log.error('Connection %s encountered an exception: %s' % (self.name, str(e)))
            halt.set()
        finally:
            if halt.is_set():
                print('Connection %s shut down...' % self.name)

    async def _connect(self, con: BleakClient) -> None:
        log = logging.getLogger('log')

        # Note: According to the docks, bleak generates exceptions if connecting failes under linux,
        # while only returning false on other platforms.
        # This should handle all cases.
        try:
            ok = await asyncio.wait_for(con.connect(), self.config.connection_timeout_hard)
            if not ok:
                log.warning('Failed to connect to %s!' % self.name)
                raise ActiveConnectionException()
        except BleakDBusError:
            log.warning('Failed to connect to %s: DBus Error.' % self.name)
            raise ActiveConnectionException()
        except BleakError as e:
            log.warning('Failed to connect to %s: %s' % (self.name, e))
            raise ActiveConnectionException()
        except asyncio.TimeoutError:
            log.warning('Failed to connect to %s: Timeout' % self.name)
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

    async def _check_for_timeout(self, con: BleakClient) -> None:
        log = logging.getLogger('log')

        if self.initial_connection_time is None:
            self.initial_connection_time = time.monotonic_ns()

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
                        await con.disconnect()
                        log.warning('Disconnected from %s.' % self.name)
                        raise ActiveConnectionException()

                elif self.config.initial_characterisitc_timeout is not None:

                    # Check if initial timeout expired
                    timeout = char.timeout + self.config.initial_characterisitc_timeout
                    has_been = (time.monotonic_ns() - self.initial_connection_time) / 1e9

                    if has_been > timeout:
                        log.warning('%s: Never receivied a notification for %s, disconnecting...' %
                                    (self.name, char.name))
                        await con.disconnect()
                        log.warning('Disconnected from %s.' % self.name)
                        raise ActiveConnectionException()

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

    async def do_disconnect(self) -> None:
        if self.con is not None:
            await self.con.disconnect()

        self.did_disconnect = True
