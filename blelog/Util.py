
def normalise_adr(adr: str):
    """Produce consistent address formatting to make comparisons easier"""
    return adr.lower().strip()

def normalise_char_uuid(uuid: str):
    """Produce consistent uuid formatting to make comparisons easier"""
    return uuid.lower().strip()
