from collections import deque
import logging
from typing import List

from blelog.Configuration import Configuration
from blelog.tui.TUI import TUIComponent, LogHandler


class TUI_Log(TUIComponent):
    def __init__(self, config: Configuration, max_height=10):
        self.max_height = max_height
        self.config = config

        self.q = deque(maxlen=self.max_height)

        self.log = logging.getLogger('log')
        lh = LogHandler(self.q)

        lh.setLevel(logging.INFO)
        self.log.addHandler(lh)

        if self.config.plain_ascii_tui:
            self.icon = {
                'INFO': '    ',
                'WARNING': 'WARN',
                'ERROR': 'ERR '
            }
        else:
            self.icon = {
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '‼️'
            }

    def get_lines(self) -> List[str]:
        lines = []
        for record in self.q:
            icon = self.icon[record.levelname]
            lines.append(icon + "  " + record.msg)
        return lines

    def title(self) -> str:
        return 'LOG'
