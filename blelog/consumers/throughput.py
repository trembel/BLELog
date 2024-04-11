"""
blelog/consumers/throughput.py
Consumer that calculates data throughput.

BLELog
Copyright (C) 2024 Philipp Schilk

This work is licensed under the terms of the MIT license.  For a copy, see the
included LICENSE file or <https://opensource.org/licenses/MIT>.
---------------------------------
"""

import asyncio
import logging
import time
from asyncio.locks import Event

from blelog.Configuration import Configuration
from blelog.ConsumerMgr import Consumer, NotifData


class Consumer_throughput(Consumer):
    def __init__(self, config: Configuration):
        super().__init__()
        self.config = config
        self.meas_period_start = None
        self.meas_period_total_bits = 0

    async def run(self, halt: Event):
        log = logging.getLogger('log')

        try:
            while not halt.is_set():
                await self._measure_throughput()
        except Exception as e:
            log.error('Consumer Throughput encountered an exception: %s' % str(e))
            log.exception(e)
            halt.set()
        finally:
            print('Consumer Throughput shut down...')

    async def _measure_throughput(self):
        log = logging.getLogger('log')

        # Receive more data:
        try:
            next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)  # type: NotifData
            self.input_q.task_done()

            if self.meas_period_start is None:
                self.meas_period_start = time.monotonic()

            self.meas_period_total_bits += len(next_data.data_raw)*8

        except asyncio.TimeoutError:
            pass

        # Calculate throughput:
        if self.config.throughput_period_s is None:
            return

        if self.meas_period_start is None:
            return

        delta_s = time.monotonic() - self.meas_period_start
        if delta_s > self.config.throughput_period_s:
            bits_per_second = self.meas_period_total_bits/delta_s

            if self.meas_period_total_bits > 0:
                log.info(f"RX Throughput: {bits_per_second:.4} bit/second.")

            self.meas_period_start = time.monotonic()
            self.meas_period_total_bits = 0
