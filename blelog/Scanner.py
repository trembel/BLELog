from typing import Union, List, Dict
import time
from dataclasses import dataclass
import asyncio
from asyncio import Event
import enum
from enum import Enum
import re
import logging

from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from blelog.Configuration import Configuration
from blelog.Util import normalise_adr


@enum.unique
class SeenDeviceState(Enum):
    NOT_SEEN = 0
    RECENTLY_SEEN = 1

    def __str__(self):
        return super().__str__().split('.')[1].replace('_', ' ')


@dataclass
class SeenDevice:
    adr: str
    alias: Union[str, None]

    state: SeenDeviceState
    name: Union[str, None]
    last_seen: Union[int, None]
    rssi: Union[int, None]

    def get_name_repr(self) -> str:
        if self.alias is not None:
            return self.alias
        if self.name is not None:
            return self.name
        return self.adr


class Scanner():
    def __init__(self, config: Configuration):
        self.config = config

        self.name_regexes = [re.compile(r) for r in config.connect_device_name_regexes]

        self.seen_devices = {}  # type: Dict[str, SeenDevice]

        # Pre-populate with all devices with fixed/pre-specified address:
        for adr in config.connect_device_adrs:
            self.seen_devices[adr] = SeenDevice(
                adr=adr,
                alias=config.device_aliases.get(adr, None),

                state=SeenDeviceState.NOT_SEEN,
                name=None,
                last_seen=None,
                rssi=None,
            )

    async def run(self, halt: Event):
        log = logging.getLogger('log')
        try:
            while not halt.is_set():
                # Scan
                devices = await BleakScanner.discover(timeout=self.config.scan_duration)
                t = time.monotonic_ns()

                # Update list of seen devices:
                self._update_seen_devices(devices, t)

                # Cooldown
                await asyncio.sleep(self.config.scan_cooldown)
        except Exception as e:
            log.error('Scanner encountered an exception: %s' % str(e))
            halt.set()
        finally:
            print('Scanner shut down...')

    def _update_seen_devices(self, devices: List[BLEDevice], t: int):
        for scanned_dev in devices:
            adr = normalise_adr(scanned_dev.address)

            if adr in self.seen_devices:
                # Known device, update information:
                dev = self.seen_devices[adr]
                dev.last_seen = t
                dev.name = scanned_dev.name
                dev.rssi = scanned_dev.rssi
                dev.state = SeenDeviceState.RECENTLY_SEEN

            else:
                # Unknown device, check if name matches:
                for r in self.name_regexes:
                    if r.match(scanned_dev.name):
                        # It does, add the new device:
                        new_dev = SeenDevice(
                            adr=adr,
                            alias=self.config.device_aliases.get(adr, None),
                            state=SeenDeviceState.RECENTLY_SEEN,
                            name=scanned_dev.name,
                            last_seen=t,
                            rssi=scanned_dev.rssi,
                        )
                        self.seen_devices[adr] = new_dev

            # Check for seen-recently timeouts:
            for dev in self.seen_devices.values():
                if dev.state == SeenDeviceState.RECENTLY_SEEN:
                    if dev.last_seen is not None:
                        has_been = (time.monotonic_ns() - dev.last_seen)/1e9
                        if has_been > self.config.seen_timeout:
                            dev.state = SeenDeviceState.NOT_SEEN
