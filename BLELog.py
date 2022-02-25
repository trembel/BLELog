#!/usr/bin/env python3
from asyncio.queues import Queue
import logging
from logging import FileHandler, StreamHandler
import sys
import asyncio
from asyncio import Event

from blelog.ConnectionMgr import ConnectionMgr
from blelog.Scanner import Scanner
from blelog.consumers.ConsumerMgr import ConsumerMgr
from blelog.tui.TUI import TUI
from blelog.tui.TUI_Connections import TUI_Connections
from blelog.tui.TUI_Log import TUI_Log
from blelog.tui.TUI_Scanner import TUI_Scanner

import config

import signal


async def main():
    # Grab configuration from config.py and clean it up:
    configuration = config.config
    configuration.normalise()

    # Re-route SIGINT (Interruption, i.e. due to CTRL-C) to a handler to
    # allow cleanup:
    halt_event = Event()
    panic_count = [0]

    def halt_hndlr(*_):
        print('\r\n\r\nInterrupted! Shutting down... This may take a few seconds..\r\n\r\n')
        halt_event.set()
        panic_count[0] += 1
        if panic_count[0] >= 3:
            print('[Panic Abort]')
            sys.exit(-1)

    signal.signal(signal.SIGINT, halt_hndlr)

    # Setup log:
    log = logging.getLogger('log')
    log.setLevel(logging.INFO)

    # Setup file logging:
    if configuration.log_file is not None:
        file_handler = FileHandler(configuration.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        log.addHandler(file_handler)

    # Add streamhandler to print ERROR messages to stderr:
    err_handler = StreamHandler(sys.stderr)
    err_handler.setLevel(logging.ERROR)
    log.addHandler(err_handler)

    # Create Data Consumers and Consumer Manager: # TODO DEBUG
    # consume_log2csv = None
    # consume_mgr = ConsumerMgr([consume_log2csv], configuration)

    # Create the scanner:
    scnr = Scanner(config=configuration)

    # Create the connection manager:
    void = Queue()  # TODO DEBUG
    con_mgr = ConnectionMgr(configuration, scnr, void)

    # Create the TUI:
    tui_scanner = TUI_Scanner(scnr)
    tui_conns = TUI_Connections(con_mgr, configuration)
    tui_log = TUI_Log(configuration)
    tui = TUI([
        tui_scanner,
        tui_conns,
        tui_log],
        configuration)

    try:
        log.info('Starting!')

        # Run the logger, scanner, tui, and consumer manager:
        scnr_task = asyncio.create_task(scnr.run(halt_event))
        con_mgr_task = asyncio.create_task(con_mgr.run(halt_event))
        tui_task = asyncio.create_task(tui.run(halt_event))
        # consume_mgr_task = asyncio.create_task(consume_mgr.run(halt_event)) # TODO DEBUG
        
        await asyncio.gather(scnr_task, con_mgr_task, tui_task)
        # await asyncio.gather(scnr_task, con_mgr_task, tui_task, consume_mgr_task) # TODO DEBUG
    except KeyboardInterrupt:
        print('Interrupted!')

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
