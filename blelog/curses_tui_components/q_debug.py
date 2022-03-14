from typing import List

from tabulate import tabulate

from blelog.ConnectionMgr import ConnectionMgr
from blelog.ConsumerMgr import ConsumerMgr
from blelog.consumers.log2csv import Consumer_log2csv
from blelog.TUI import CursesTUI_Component


class q_TUI(CursesTUI_Component):
    def __init__(self, con_mgr: ConnectionMgr, consum_mgr: ConsumerMgr):
        self.con_mgr = con_mgr
        self.consum_mgr = consum_mgr

    def get_lines(self) -> List[str]:

        q_s = {}

        q_s['Connections Output'] = self.con_mgr.output_queue


        for consumer in self.consum_mgr.consumers:
            q_s[str(consumer.__class__.__name__)] = consumer.input_q

            if isinstance(consumer, Consumer_log2csv):
                for output in consumer.file_outputs.values():
                    q_s[output.file_path] = output.input_q

        rows = []
        row = []

        for name, q in q_s.items():
            if len(row) == 2*3:
                rows.append(row)
                row = []
            row.append(str(name))
            row.append(str(q.qsize()))
        rows.append(row)

        return tabulate(rows, tablefmt='plain').splitlines()

    def title(self) -> str:
        return 'QUEUES'
