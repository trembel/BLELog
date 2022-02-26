import asyncio
from asyncio.locks import Event
from typing import Union
import logging

import multiprocessing as mp
import queue

from blelog.Configuration import Configuration
from blelog.consumers.ConsumerMgr import Consumer, NotifData

from plot import plot


class Consumer_plotter(Consumer):
    def __init__(self, config: Configuration):
        super().__init__()
        self.config = config
        self.do_toggle_on_off = False

    async def run(self, halt: Event):
        log = logging.getLogger('log')

        plotting_process = None
        plotting_queue = None  # type: Union[mp.Queue, None]

        mp.set_start_method('spawn')

        try:
            while not halt.is_set():

                if self.do_toggle_on_off:
                    self.do_toggle_on_off = False

                    if plotting_process is None:
                        plotting_queue = mp.Queue()
                        plotting_process = mp.Process(target=plot, args=(plotting_queue,))
                        plotting_process.start()
                    else:
                        plotting_process.kill()
                        plotting_queue = None

                try:
                    next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)  # type: NotifData
                    self.input_q.task_done()

                    if plotting_process is not None and plotting_queue is not None:
                        while True:
                            try:
                                plotting_queue.put_nowait(next_data)
                                break
                            except queue.Full:
                                pass

                except asyncio.TimeoutError:
                    pass
        except Exception as e:
            log.error('Consumer Server encountered an exception: %s' % str(e))
            halt.set()
        finally:
            print('Consumer Server shut down...')

    def toggle_on_off(self):
        self.do_toggle_on_off = True
