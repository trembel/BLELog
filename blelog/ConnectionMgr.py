from asyncio.queues import Queue
from asyncio.tasks import Task
import logging
import asyncio
from asyncio import Event
from dataclasses import dataclass
import time
from typing import Union, Dict

from blelog.ActiveConnection import ActiveConnection, ConnectionState
from blelog.Configuration import Configuration
from blelog.Scanner import Scanner, SeenDevice, SeenDeviceState


@dataclass
class ManagedConnection():
    last_connection_attempt: Union[int, None]
    scanner_information: SeenDevice
    active_connection: Union[None, ActiveConnection]

    def state(self) -> ConnectionState:
        if self.active_connection is None:
            return ConnectionState.DISCONNECTED
        else:
            return self.active_connection.state

    def ready_to_connect(self) -> bool:
        if self.state() == ConnectionState.DISCONNECTED:
            if self.scanner_information.state == SeenDeviceState.RECENTLY_SEEN:
                return True
        return False

    # 'Less than' comparison for managed connections.
    # Used to find connection that has not attempted to connect for
    # the longest time.
    def __lt__(self, other):
        if self.last_connection_attempt is None:
            return True
        elif other.last_connection_attempt is None:
            return False
        else:
            return self.last_connection_attempt < other.last_connection_attempt


class ConnectionMgr():
    def __init__(self, config: Configuration, scnr: Scanner, output_queue: Queue):
        self.config = config
        self.scnr = scnr
        self.connections = {}  # type: Dict[str, ManagedConnection]
        self.tasks = []
        self.output_queue = output_queue

    async def run(self, halt: Event):
        log = logging.getLogger('log')
        try:
            while not halt.is_set():
                self._update_connection_information()
                self._manage_connections(halt)
                await asyncio.sleep(self.config.mgr_interval)

        except Exception as e:
            log.error('ConnectiongMgr encountered an exception: %s' % str(e))
            halt.set()
        finally:
            await asyncio.gather(*self.tasks)
            print('ConnectionMgr shut down...')

    def _update_connection_information(self):
        # Pickup new devices/updates from scanner:
        for seen_device in self.scnr.seen_devices.values():
            if seen_device.adr in self.connections:
                con = self.connections[seen_device.adr]
                con.scanner_information = seen_device
            else:
                con = ManagedConnection(
                    last_connection_attempt=None,
                    scanner_information=seen_device,
                    active_connection=None,
                )
                self.connections[seen_device.adr] = con

        # Cleanup dropped connections:
        for d in self.connections.values():
            if d.state() == ConnectionState.DISCONNECTED:
                d.active_connection = None

    def _manage_connections(self, halt: Event):
        log = logging.getLogger('log')

        # Count active and connecting connections
        active_connection_count = 0
        connecting_connection_count = 0
        for d in self.connections.values():
            if d.state() == ConnectionState.CONNECTED:
                active_connection_count += 1
            if d.state() == ConnectionState.CONNECTING:
                active_connection_count += 1
                connecting_connection_count += 1

        # If there is space for more connections, spawn one:
        if active_connection_count < self.config.max_active_connections:
            if connecting_connection_count < self.config.max_simulatneous_connection_attempts:
                # First, find all possible connections:
                possible_connections = [c for c in self.connections.values() if c.ready_to_connect()]

                if len(possible_connections) != 0:

                    # Prioritise Connections that have never been connected, or whose
                    # last connection attempt lies further back:
                    possible_connections.sort()
                    next_con = possible_connections[0]

                    log.info('Attempting to connect to %s' % next_con.scanner_information.get_name_repr())
                    next_con.last_connection_attempt = time.monotonic_ns()
                    adr = next_con.scanner_information.adr
                    name = next_con.scanner_information.get_name_repr()

                    next_con.active_connection = ActiveConnection(adr, name, self.config, self.output_queue)
                    task = asyncio.create_task(next_con.active_connection.run(halt))
                    self.tasks.append(task)
