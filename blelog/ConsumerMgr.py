"""
blelog/ConsumerMgr.py
Receives all data from all connections, and distributes it to all data consumers.
(CSV Logging, Live plotting..)

BLELog
Copyright (C) 2024 Philipp Schilk

This work is licensed under the terms of the MIT license.  For a copy, see the 
included LICENSE file or <https://opensource.org/licenses/MIT>.
---------------------------------
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from asyncio import Event, Queue
from asyncio.queues import QueueFull
from dataclasses import dataclass
from typing import Any, List, Union

from blelog.Configuration import Characteristic, Configuration

warn_thsh = 300
warn_timeout_ns = 60e9


class Consumer(ABC):
    """
    Basic interface for a data consumer.
    """

    def __init__(self) -> None:
        self.input_q = Queue()
        self.last_full_queue_warning = None  # type: Union[int, None]

    @abstractmethod
    async def run(self, halt: Event) -> None:
        pass

    def should_queue_warn(self) -> bool:
        if self.last_full_queue_warning is None:
            return True
        else:
            return self.last_full_queue_warning + warn_timeout_ns < time.monotonic_ns()


@dataclass
class NotifData:
    device_adr: str
    device_name_repr: str
    characteristic: Characteristic
    data: List[List[Any]]
    data_raw: bytearray


class ConsumerMgr:
    def __init__(self, config: Configuration) -> None:
        self.config = config
        self.consumers = []  # type: List[Consumer]
        self.consumer_tasks = []
        self.input_q = Queue()

    def add_consumer(self, c: Consumer):
        self.consumers.append(c)

    async def run(self, halt: Event) -> None:
        log = logging.getLogger('log')
        try:
            # Spinup all consumers:
            self._launch_consumers(halt)

            while not (halt.is_set() and self.input_q.empty()):
                await self._distribute_data()
                self._monitor_timeouts()

        except Exception as e:
            log.error('ConsumerMgr encountered an exception: %s' % str(e))
            log.exception(e)
            halt.set()
        finally:
            total_output_q = sum([c.input_q.qsize() for c in self.consumers])
            if total_output_q > 0:
                print('ConsumerMgr ready to shut down. Waiting for %i items in output queues...' % total_output_q)
            await asyncio.gather(*self.consumer_tasks)
            print('ConsumerMgr shut down...')

    def _launch_consumers(self, halt: Event) -> None:
        log = logging.getLogger('log')
        for consumer in self.consumers:
            tsk = asyncio.create_task(consumer.run(halt))
            self.consumer_tasks.append(tsk)
            log.info('Consumer %s enabled!' % consumer.__class__.__name__)

    async def _distribute_data(self):
        log = logging.getLogger('log')
        try:
            # Grab data, distribute to all consumers:
            next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)
            for consumer in self.consumers:
                try:
                    consumer.input_q.put_nowait(next_data)
                except QueueFull:
                    log.warning('Consumer %s did not accept data!' % type(consumer).__name__)
            self.input_q.task_done()

        except asyncio.TimeoutError:
            pass

    def _monitor_timeouts(self):
        log = logging.getLogger('log')
        # Check if any consumers are lagging behind:
        for consumer in self.consumers:
            if consumer.input_q.qsize() > warn_thsh:
                log.warning('The input queue of consumer %s has more than %i items, is the consumer keeping up?'
                            % (type(consumer).__name__, consumer.input_q.qsize()))
                consumer.last_full_queue_warning = time.monotonic_ns()
