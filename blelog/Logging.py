"""
blelog/Logger.py
Configures the global status logger, including log-file output.

BLELog
Copyright (C) 2024 Philipp Schilk

This work is licensed under the terms of the MIT license.  For a copy, see the 
included LICENSE file or <https://opensource.org/licenses/MIT>.
---------------------------------
"""

import logging
from logging import FileHandler
# import sys
# from StreamHandler

from blelog.Configuration import Configuration


class LogReroute(logging.Handler):
    def __init__(self, output_logger_name: str):
        super().__init__()
        self.output_logger_name = output_logger_name

    def handle(self, record: logging.LogRecord) -> bool:
        new_logger = logging.getLogger(self.output_logger_name)
        new_logger.log(record.levelno, record.getMessage())
        return True


def setup_logging(config: Configuration):  # Setup log:
    log = logging.getLogger('log')
    log.setLevel(logging.INFO)

    # Reroute warnings to log:
    logging.captureWarnings(True)
    warn_logger = logging.getLogger('py.warnings')
    warn_logger.setLevel(logging.WARNING)
    warn_logger.addHandler(LogReroute('log'))

    # Setup status log file output:
    if config.log_file is not None:
        file_handler = FileHandler(config.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        log.addHandler(file_handler)

    # Add stream handler to print ERROR messages to stderr:
    # err_handler = StreamHandler(sys.stderr)
    # err_handler.setLevel(logging.ERROR)
    # log.addHandler(err_handler)
