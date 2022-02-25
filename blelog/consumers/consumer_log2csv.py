import asyncio
from asyncio.locks import Event
from asyncio.queues import Queue
import logging
import aiofiles

from blelog.Configuration import Configuration
from blelog.consumers.ConsumerMgr import Consumer, NotifData


class Consumer_log2csv(Consumer):
    def __init__(self, config: Configuration):
        self.config = config

    async def run(self, halt: Event, input: Queue):
        # TODO: This could be changed/seperated to have seperate consumer per connection/characterisitc?
        log = logging.getLogger('log')
        files = {}
        try:
            while not halt.is_set():
                while not input.empty():
                    try:
                        next_data = await asyncio.wait_for(input.get(), timeout=0.5)  # type: NotifData
                        file_name = self.file_name(next_data.device_adr, next_data.characteristic.uuid)
                        if file_name in files:
                            # File already open, write:
                            pass
                        else:
                            # File not yet open, write:
                            pass

                    except asyncio.TimeoutError:
                        pass
        except Exception as e:
            log.error('Consumer log2csv encountered an exception: %s' % str(e))
            halt.set()
        finally:
            for f in files:
                pass
            print('Consumer log2csv shutdown...')

    def file_name(self, device_adr, char_uuid):
        n = "%s_%s.csv" % (device_adr, char_uuid)
        return n.replace(' ', '_')
