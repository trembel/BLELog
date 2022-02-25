import tabulate
import time
from typing import List

from blelog.Scanner import Scanner, SeenDeviceState
from blelog.tui.TUI import TUIComponent


class TUI_Scanner(TUIComponent):
    def __init__(self, scnr: Scanner, config):
        self.scnr = scnr

        if config.plain_ascii_tui:
            self.state_icon = {
                SeenDeviceState.RECENTLY_SEEN: '',
                SeenDeviceState.NOT_SEEN: '',
            }
        else:
            self.state_icon = {
                SeenDeviceState.RECENTLY_SEEN: '✅ ',
                SeenDeviceState.NOT_SEEN: '❔ ',
            }

    def get_lines(self) -> List[str]:
        scnr = self.scnr
        headers = ['Name', 'Address', 'State', 'Time Since Scan (s)', 'RSSI']
        rows = []

        for d in scnr.seen_devices.values():
            name = d.get_name_repr()
            adr = d.adr
            state = self.state_icon[d.state] + str(d.state)

            if d.last_seen is not None:
                t = round((time.monotonic_ns() - d.last_seen)/1e9, 2)
            else:
                t = ''

            if d.state == SeenDeviceState.RECENTLY_SEEN and d.rssi is not None:
                rssi = str(d.rssi)
            else:
                rssi = ''

            rows.append([name, adr, state, t, rssi])

        return tabulate.tabulate(rows, headers, tablefmt='plain').splitlines()

    def title(self) -> str:
        return 'SCANNER'
