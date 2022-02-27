"""
char_decoders.py
Characteristic data decoding.

BLELog - Philipp Schilk, 2022
PBL, ETH Zuerich
---------------------------------

Decoder functions used to convert the raw bytearray received
from characteristic notifications into actual data.

Should return a list of data rows.
Data rows in turn a list of data, usually numbers.

Each data row should be of the same length as the column_headers
set for the characteristic in config.py where this decoder is used.

Confusing, I know, I'm sorry.

An example:
Each PPG data-point consists of a package index and an actual reading.
The column headers are defined as follows:

    column_headers=['index', 'ppg red']

The decode_ppg  function, assuming the package index is 1 and
the readings are [10, 20, 30], will return the following list:

    [[1, 10],
     [1, 20],
     [1, 30]]

IMPORTANT: If you wish to print any debug information, **do not** use
print(...) - The output will likely be lost depending on the TUI used.
Instead, get a logger as follows:

    log = logging.getLogger('log')

And use it to print instead:

    log.info('...')
    log.warning('...')
    log.error('...')

"""
import logging
from typing import Any, List
import struct


def decode_ppg(data: bytearray) -> List[List[Any]]:
    log = logging.getLogger('log')

    # Confirm data length:
    if len(data) != 204:
        log.warning('Malformed PPG data, rejecting...')
        return []

    # Decode:
    *samples, index = struct.unpack('<50ii', data)

    return [[index, s] for s in samples]


def decode_acc_gyr_qvar(data: bytearray) -> List[List[Any]]:
    log = logging.getLogger('log')

    # Confirm data length:
    if len(data) != 244:
        log.warning('Malformed acc/gyr/qvar data, rejecting...')
        return []

    # Decode:
    *samples, index = struct.unpack('<120hi', data)

    return [[index, s] for s in samples]


def decode_temp(data: bytearray) -> List[List[Any]]:
    log = logging.getLogger('log')

    # Confirm data length:
    if len(data) != 64:
        log.warning('Malformed temp, rejecting...')
        return []

    # Decode:
    *samples, index = struct.unpack('<30hi', data)

    return [[index, s] for s in samples]
