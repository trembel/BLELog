from abc import ABC, abstractmethod
from asyncio.queues import QueueFull
from dataclasses import dataclass
import logging
import time
from typing import Any, List, Union
import asyncio
from asyncio import Event, Queue

from blelog.Configuration import Characteristic, Configuration

warn_thsh = 300
warn_timeout_ns = 60e9


class Consumer(ABC):
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
            for consumer in self.consumers:
                tsk = asyncio.create_task(consumer.run(halt))
                self.consumer_tasks.append(tsk)
                log.info('Consumer %s enabled!' % consumer.__class__.__name__)

            while not halt.is_set():
                try:
                    # Grab data, distribute to all consumers:
                    next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)
                    for consumer in self.consumers:
                        try:
                            consumer.input_q.put_nowait(next_data)
                        except QueueFull:
                            log.warning('Consumer %s did not accept data!' % type(consumer).__name__)
                    self.input_q.task_done()

                    # Check if any consumers are lagging behind:
                    for consumer in self.consumers:
                        if consumer.input_q.qsize() > warn_thsh:
                            log.warning('The input queue of consumer %s has more than %i items, is the consumer keeping up?'
                                        % (type(consumer).__name__, consumer.input_q.qsize()))
                            consumer.last_full_queue_warning = time.monotonic_ns()

                except asyncio.TimeoutError:
                    pass

        except Exception as e:
            log.error('ConsumerMgr encountered an exception: %s' % str(e))
            halt.set()
        finally:
            await asyncio.gather(*self.consumer_tasks)
            print('ConsumerMgr shut down...')
