"""
blelog/curses_tui_component/q_debug_TUI.py
TUI Component that shows queue size for throughput debugging.

BLELog
Copyright (C) 2024 Philipp Schilk

This work is licensed under the terms of the MIT license.  For a copy, see the 
included LICENSE file or <https://opensource.org/licenses/MIT>.
---------------------------------
"""
from dataclasses import dataclass
from typing import List

from blelog.ConnectionMgr import ConnectionMgr
from blelog.ConsumerMgr import ConsumerMgr
from blelog.consumers.log2csv import Consumer_log2csv
from blelog.TUI import CursesTUI_Component


@dataclass
class q_info:
    name: str
    size: int


class q_TUI(CursesTUI_Component):
    def __init__(self, con_mgr: ConnectionMgr, consum_mgr: ConsumerMgr):
        self.con_mgr = con_mgr
        self.consum_mgr = consum_mgr

    def get_lines(self) -> List[str]:

        q_s = []

        q_s.append(q_info('Connection Output', self.con_mgr.output_queue.qsize()))

        for consumer in self.consum_mgr.consumers:
            i = q_info(
                name=consumer.__class__.__name__,
                size=consumer.input_q.qsize()
            )
            q_s.append(i)

            if isinstance(consumer, Consumer_log2csv):
                for output in consumer.file_outputs.values():
                    i = q_info(
                        name=output.file_path,
                        size=output.input_q.qsize()
                    )
                    q_s.append(i)

        total_len = sum([q.size for q in q_s])

        rows = [
            'Total queue length: %i' % total_len,
            'Largest queues:']

        row = ""
        q_s.sort(key=lambda x: -x.size)
        for i in range(min(4, len(q_s))):
            q = q_s[i]
            row += ("%s: %i   " % (q.name, q.size))

        rows.append(row)

        return rows

    def title(self) -> str:
        return 'QUEUES'
