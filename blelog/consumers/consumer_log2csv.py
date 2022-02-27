import asyncio
from asyncio.locks import Event
from asyncio.queues import Queue
from typing import List
import logging
import aiofiles
import os
import csv
import io

from blelog.Configuration import Configuration
from blelog.consumers.ConsumerMgr import Consumer, NotifData


class CSVLogger:
    def __init__(self, file_path: str, column_headers: List[str]):
        self.file_path = file_path
        self.input_q = Queue()
        self.column_headers = column_headers
        self.active = True

    async def run(self, halt: Event):
        log = logging.getLogger('log')
        f = None

        try:
            if os.path.exists(self.file_path):
                f = await aiofiles.open(self.file_path, 'a', newline='')
                # log.info('Opened %s' % self.file_path)
            else:
                f = await aiofiles.open(self.file_path, 'w', newline='')
                await self.write_row(f, self.column_headers)
                # log.info('Created %s' % self.file_path)

            while not halt.is_set():
                try:
                    next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)  # type: NotifData
                    for row in next_data.data:
                        await self.write_row(f, row)
                except asyncio.TimeoutError:
                    pass
        except FileNotFoundError as e:
            log.error('CSVLogger %s encountered an exception: %s' % (self.file_path, str(e)))
        except Exception as e:
            log.error('CSVLogger %s encountered an exception: %s' % (self.file_path, str(e)))
            halt.set()
        finally:
            self.active = False
            if f is not None:
                await f.close()
            # print('CSVLogger %s shut down...' % self.file_path)

    async def write_row(self, f, row):
        row_str_io = io.StringIO()
        csv_writer = csv.writer(row_str_io)
        csv_writer.writerow(row)
        await f.write(row_str_io.getvalue())


class Consumer_log2csv(Consumer):
    def __init__(self, config: Configuration):
        super().__init__()
        self.config = config

    async def run(self, halt: Event):
        log = logging.getLogger('log')
        file_outputs = {}
        tasks = []

        try:
            while not halt.is_set():
                try:
                    next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)  # type: NotifData
                    file_path = self.file_path(next_data.device_adr, next_data.characteristic)
                    if file_path not in file_outputs:
                        file_outputs[file_path] = CSVLogger(file_path, next_data.characteristic.column_headers)
                        tasks.append(asyncio.create_task(file_outputs[file_path].run(halt)))
                    if file_outputs[file_path].active:
                        await file_outputs[file_path].input_q.put(next_data)
                except asyncio.TimeoutError:
                    pass
        except Exception as e:
            log.error('Consumer log2csv encountered an exception: %s' % str(e))
            halt.set()
        finally:
            await asyncio.gather(*tasks)
            print('Consumer log2csv shut down...')

    def file_path(self, device_adr, char):
        if device_adr in self.config.device_aliases:
            name = self.config.device_aliases[device_adr]
        else:
            name = device_adr

        n = "%s_%s.csv" % (name, char.name)
        n = n.replace(' ', '_')
        return os.path.join(self.config.log2csv_folder_name, n)
