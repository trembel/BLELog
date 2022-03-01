"""
blelog/curses_tui_components/Connections_TUI.py
'Connections' Section of the curses dashboard.

BLELog - Philipp Schilk, 2022
PBL, ETH Zuerich
---------------------------------
"""
from typing import List
import tabulate
import time

from blelog.Configuration import Configuration
from blelog.TUI import CursesTUI_Component
from blelog.ConnectionMgr import ConnectionMgr
from blelog.ActiveConnection import ConnectionState


class Connections_TUI(CursesTUI_Component):
    def __init__(self, mgr: ConnectionMgr, config: Configuration):
        self.mgr = mgr
        self.config = config

        if config.plain_ascii_tui:
            self.state_icon = {
                ConnectionState.DISCONNECTED: '',
                ConnectionState.CONNECTING: '',
                ConnectionState.CONNECTED: '',
            }
        else:
            self.state_icon = {
                ConnectionState.DISCONNECTED: '❌ ',
                ConnectionState.CONNECTING: '💡 ',
                ConnectionState.CONNECTED: '✅ ',
            }

    def get_lines(self) -> List[str]:
        mgr = self.mgr
        header = ['']
        conn_state_row = ['']
        conn_time_row = ['']
        char_rows = {c.uuid: [c.name] for c in mgr.config.characteristics}
        for con in mgr.connections.values():

            if con.active_connection is None or con.active_connection.state == ConnectionState.DISCONNECTED:
                continue

            header.append(con.scanner_information.get_name_repr())

            state = con.state()
            conn_state_row.append(self.state_icon[state]+str(state))

            conn_time_row.append(con.active_connection.active_time_str())

            for char in self.config.characteristics:
                t_ns = con.active_connection.last_notif[char.uuid]
                if t_ns is not None:
                    t = str(round((time.monotonic_ns() - t_ns)/1e9, 2))
                else:
                    t = 'x'
                char_rows[char.uuid].append(t)

        rows = [conn_state_row, conn_time_row, *char_rows.values()]
        return tabulate.tabulate(rows, header, tablefmt='plain').splitlines()

    def title(self) -> str:
        return 'ACTIVE CONNECTIONS'
