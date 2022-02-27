"""
blelog/Util.py
Utility functions.

BLELog - Philipp Schilk, 2022
PBL, ETH Zuerich
---------------------------------
"""


def normalise_adr(adr: str):
    """Produce consistent address formatting to make comparisons easier"""
    return adr.lower().strip()


def normalise_char_uuid(uuid: str):
    """Produce consistent uuid formatting to make comparisons easier"""
    return uuid.lower().strip()
