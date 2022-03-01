from collections import defaultdict
import asyncio
from asyncio import Event
import logging
from blelog.ConsumerMgr import Consumer, NotifData


class Consumer_SPIndexChecker(Consumer):

    async def run(self, halt: Event) -> None:
        log = logging.getLogger('log')

        # Track last notification index for each char of each device:
        last_index_store = defaultdict(lambda: defaultdict(lambda: None))

        try:
            while not halt.is_set():
                try:
                    next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)  # type: NotifData

                    # This relies on the output-format of the char_decoders!
                    index = next_data.data[0][0]
                    adr = next_data.device_adr
                    name = next_data.device_name_repr
                    char_name = next_data.characteristic.name
                    uuid = next_data.characteristic.uuid

                    # Check if there was a previous index:
                    last_index = last_index_store[adr][uuid]

                    if last_index is not None:
                        if index != last_index + 1:
                            log.warning("IndexChecker: %s: %s index discontinuity %i -> %i" % (name, char_name, last_index, index))

                    # Set new last index
                    last_index_store[adr][uuid] = index
                except asyncio.TimeoutError:
                    pass

        except Exception as e:
            log.error('SP-Index Checker %s encountered an exception: %s' % str(e))
            halt.set()
