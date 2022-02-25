from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import List
import asyncio
from asyncio import Event, Queue

from blelog.Configuration import Characteristic, Configuration


class Consumer(ABC):
    @abstractmethod
    async def run(self, halt: Event, input: Queue) -> None:
        pass


@dataclass
class NotifData:
    device_adr: str
    device_name_repr: str
    characteristic: Characteristic
    data: List[float]


class ConsumerMgr:
    def __init__(self, consumers: List[Consumer], config: Configuration) -> None:
        self.config = config
        self.consumers = consumers
        self.consumer_tasks = []
        self.input = Queue()
        self.outputs = []  # type: List[Queue]

    async def run(self, halt: Event) -> None:
        log = logging.getLogger('log')
        try:
            # Spinup all consumers:
            for consumer in self.consumers:
                consumer_input = Queue()
                self.outputs.append(consumer_input)
                tsk = asyncio.create_task(consumer.run(halt, consumer_input))
                self.consumer_tasks.append(tsk)

            while not halt.is_set():
                try:
                    next_data = await asyncio.wait_for(self.input.get(), timeout=0.5)
                    for out in self.outputs:
                        await out.put(next_data)
                except asyncio.TimeoutError:
                    pass

        except Exception as e:
            log.error('ConsumerMgr encountered an exception: %s' % str(e))
            halt.set()
        finally:
            await asyncio.gather(*self.consumer_tasks)
            print('ConsumerMgr Shutdown...')
