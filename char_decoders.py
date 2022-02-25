import logging
from typing import Any, List
import struct


def decode_ppg(data: bytearray) -> List[List[Any]]:
    # Confirm data length:
    log = logging.getLogger('log')
    if len(data) != 204:
        log.warning('Malformed PPG data, rejecting...')
        return []

    # Decode:
    *samples, index = struct.unpack('<50ii', data)

    return [[index, s] for s in samples]


def decode_acc_gyr_qvar(data: bytearray) -> List[List[Any]]:
    # Confirm data length:
    log = logging.getLogger('log')
    if len(data) != 244:
        log.warning('Malformed acc/gyr/qvar data, rejecting...')
        return []

    # Decode:
    *samples, index = struct.unpack('<120hi', data)

    return [[index, s] for s in samples]


def decode_temp(data: bytearray) -> List[List[Any]]:
    # Confirm data length:
    log = logging.getLogger('log')
    if len(data) != 64:
        log.warning('Malformed temp, rejecting...')
        return []

    # Decode:
    *samples, index = struct.unpack('<30hi', data)

    return [[index, s] for s in samples]
