from dataclasses import dataclass
from typing import Callable, List, Dict, Union
from enum import Enum
import enum

from blelog.Util import normalise_adr, normalise_char_uuid


@enum.unique
class TUI_Mode(Enum):
    CURSE = 0
    CONSOLE = 1


@dataclass
class Characteristic:
    name: str
    uuid: str
    timeout: Union[None, float]
    column_headers: List[str]
    data_decoder: Callable


@dataclass
class Configuration:
    scan_duration: float
    scan_cooldown: float
    seen_timeout: float

    max_active_connections: int
    max_simulatneous_connection_attempts: int
    connection_timeout_scan: int
    connection_timeout_hard: int

    connect_device_name_regexes: List[str]
    connect_device_adrs: List[str]
    device_aliases: Dict[str, str]

    characteristics: List[Characteristic]
    initial_characterisitc_timeout: float

    mgr_interval: float

    log2csv_enabled: bool
    log2csv_folder_name: str

    plotter_open_by_default: bool
    plotter_exit_on_plot_close: bool

    log_file: str

    plain_ascii_tui: bool
    tui_mode: TUI_Mode
    curse_tui_interval: float

    # consumers: List[Consumers]

    def normalise(self):
        # normalise connect device addreses:
        self.connect_device_adrs = [normalise_adr(adr) for adr in self.connect_device_adrs]

        # normalise connect device addreses in list of aliases:
        self.device_aliases = {normalise_adr(adr): alias for adr, alias in self.device_aliases.items()}

        # normalise characeritic UUIDs:
        for char in self.characteristics:
            char.uuid = normalise_char_uuid(char.uuid)

        # Check for duplicate characteristic UUIDs:
        uuids = []
        for char in self.characteristics:
            if char.uuid in uuids:
                print('Duplicate characteristic UUID %s' % str(char.uuid))
                exit(-1)
            uuids.append(char.uuid)

    def get_characteristic(self, uuid: str) -> Characteristic:
        for c in self.characteristics:
            if c.uuid == normalise_char_uuid(uuid):
                return c
        raise KeyError()
