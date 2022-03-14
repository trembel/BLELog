"""
blelog/consumers/plotter.py
Data consumer that displays data in a live plot

BLELog - Philipp Schilk, 2022
PBL, ETH Zuerich
---------------------------------

Matplotlib plot is defined in plot.py.
plot.py runs in its own process - see plot.py for details.
"""

import asyncio
import logging
import multiprocessing as mp
import queue
import signal
from asyncio.locks import Event
from logging import LogRecord
from logging.handlers import QueueHandler

from blelog.Configuration import Configuration
from blelog.ConsumerMgr import Consumer, NotifData
from plot import plot


class PlottingProcess(mp.Process):
    def __init__(self) -> None:
        super().__init__()
        self.input_q = mp.Queue()
        self.log_q = mp.Queue()

    def run(self) -> None:
        # Ignore interrupt signals in the plotting process,
        # BLELog will take care of closing the process:
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # Setup logging:
        # Reroute 'log' and warnings to output queue:
        log = logging.getLogger('log')
        log.setLevel(logging.DEBUG)
        log.addHandler(QueueHandler(self.log_q))

        logging.captureWarnings(True)
        log_warn = logging.getLogger('py.warnings')
        log_warn.setLevel(logging.WARNING)
        log_warn.addHandler(QueueHandler(self.log_q))

        try:
            plot(self.input_q)
        except Exception as e:
            log.error("Plotter encountered an exception!")
            log.exception(e)


class Consumer_plotter(Consumer):
    def __init__(self, config: Configuration):
        super().__init__()
        self.config = config
        self.do_toggle_on_off = False
        self.plotting_process = None

    async def run(self, halt: Event):
        log = logging.getLogger('log')
        mp.set_start_method('spawn')

        if self.config.plotter_open_by_default:
            self.plotting_process = PlottingProcess()
            self.plotting_process.start()
            log.info('Opened plotter GUI.')

        try:
            while not halt.is_set():
                self._monitor_plotter_process(halt)
                self._open_close_plotter()
                self._grab_logs()
                await self._stream_data()

        except Exception as e:
            log.error('Consumer Plotter encountered an exception: %s' % str(e))
            halt.set()
        finally:
            if self.plotting_process is not None:
                self.plotting_process.kill()
            print('Consumer Plotter shut down...')

    def _monitor_plotter_process(self, halt: Event):
        log = logging.getLogger('log')

        if self.plotting_process is not None and not self.plotting_process.is_alive():
            # Look for and print any messages placed into the error queue:
            self._grab_logs()

            log.info('Plotter GUI closed.')
            self.plotting_process = None

            if self.config.plotter_exit_on_plot_close:
                log.error('Shutting down...')
                log.error('See \'plotter_exit_on_plot_close\' to change this behaviour!')
                halt.set()

    def _open_close_plotter(self):
        log = logging.getLogger('log')

        # Check if toggling the plot was requested:
        if self.do_toggle_on_off:
            self.do_toggle_on_off = False

            if self.plotting_process is None:
                self.plotting_process = PlottingProcess()
                self.plotting_process.start()
                log.info('Opened plotter GUI.')
            else:
                self._grab_logs()
                self.plotting_process.kill()
                self.plotting_process = None
                log.info('Closed plotter GUI.')

    async def _stream_data(self):
        log = logging.getLogger('log')
        try:
            # Wait for new data:
            next_data = await asyncio.wait_for(self.input_q.get(), timeout=0.5)  # type: NotifData
            self.input_q.task_done()

            # Try to pass the data to the plotting process if there is one
            if self.plotting_process is not None:
                attempts = 0
                while attempts < 10:
                    try:
                        self.plotting_process.input_q.put_nowait(next_data)
                        break
                    except queue.Full:
                        attempts += 1
                        await asyncio.sleep(0.05)
                else:
                    # Failed to put into queue 10 times, log and move on:
                    log.warning('Consumer Plotter: Failed to pass data to logging process!')

        except asyncio.TimeoutError:
            pass

    def _grab_logs(self):
        log = logging.getLogger('log')
        if self.plotting_process is not None:
            while True:
                try:
                    record = self.plotting_process.log_q.get_nowait()  # type: LogRecord
                    log.log(record.levelno, record.getMessage())
                except queue.Empty:
                    break

    def toggle_on_off(self):
        self.do_toggle_on_off = True
