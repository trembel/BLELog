#!/usr/bin/env python3
import asyncio
import logging
import signal
import sys
from asyncio import Event
from asyncio.queues import Queue
from logging import FileHandler, StreamHandler

import config
from blelog.ConnectionMgr import ConnectionMgr
from blelog.consumers.consumer_log2csv import Consumer_log2csv
from blelog.consumers.ConsumerMgr import ConsumerMgr
from blelog.Scanner import Scanner
from blelog.tui.TUI import TUI
from blelog.tui.TUI_Connections import TUI_Connections
from blelog.tui.TUI_Log import TUI_Log
from blelog.tui.TUI_Scanner import TUI_Scanner


async def main():
    # Grab configuration from config.py and clean it up:
    configuration = config.config
    configuration.normalise()

    # Setup log:
    log = logging.getLogger('log')
    log.setLevel(logging.INFO)

    # Setup status log file output:
    if configuration.log_file is not None:
        file_handler = FileHandler(configuration.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        log.addHandler(file_handler)

    # Add streamhandler to print ERROR messages to stderr:
    err_handler = StreamHandler(sys.stderr)
    err_handler.setLevel(logging.ERROR)
    log.addHandler(err_handler)

    # Create Data Consumers and Consumer Manager:
    consume_log2csv = Consumer_log2csv(configuration)
    consume_mgr = ConsumerMgr([consume_log2csv], configuration)

    # Create the scanner:
    scnr = Scanner(config=configuration)

    # Create the connection manager:
    con_mgr = ConnectionMgr(configuration, scnr, consume_mgr.input_q)

    # Create the TUI:
    tui = TUI(configuration)

    tui_scanner = TUI_Scanner(scnr, configuration)
    tui.add_component(tui_scanner)
    tui_conns = TUI_Connections(con_mgr, configuration)
    tui.add_component(tui_conns)
    tui_log = TUI_Log(configuration)
    tui.add_component(tui_log)

    # Re-route SIGINT (Interruption, i.e. due to CTRL-C) to a handler to
    # allow cleanup:
    halt_event = Event()
    panic_count = [0]

    def halt_hndlr(*_):
        # Set halt event
        print('\r\n [%i] Interrupted! Shutting down... This may take a few seconds..\r\n' % panic_count[0])
        halt_event.set()

        # immediatly turn of TUI:
        tui.off()

        # If this happends 3 times, kill the program:
        panic_count[0] += 1
        if panic_count[0] >= 3:
            print('[Panic Abort]')
            sys.exit(-1)

    signal.signal(signal.SIGINT, halt_hndlr)
    tui.set_halt_handler(halt_hndlr)

    # Startup:
    log.info('Starting!')

    # Run the logger, scanner, tui, and consumer manager:
    scnr_task = asyncio.create_task(scnr.run(halt_event))
    con_mgr_task = asyncio.create_task(con_mgr.run(halt_event))
    tui_task = asyncio.create_task(tui.run(halt_event))
    consume_mgr_task = asyncio.create_task(consume_mgr.run(halt_event))

    await asyncio.gather(scnr_task, con_mgr_task, tui_task, consume_mgr_task)

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
