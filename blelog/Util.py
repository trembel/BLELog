"""
blelog/Util.py
Utility functions.

BLELog
Copyright (C) 2024 Philipp Schilk

This work is licensed under the terms of the MIT license.  For a copy, see the 
included LICENSE file or <https://opensource.org/licenses/MIT>.
---------------------------------
"""


def normalise_adr(adr: str):
    """Produce consistent address formatting to make comparisons easier"""
    return adr.lower().strip()


def normalise_char_uuid(uuid: str):
    """Produce consistent uuid formatting to make comparisons easier"""
    return uuid.lower().strip()
