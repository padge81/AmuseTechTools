from .exceptions import EdidChecksumError


def checksum_is_valid(edid: bytes) -> bool:
    return sum(edid) % 256 == 0


def fix_checksum(edid: bytes) -> bytes:
    if len(edid) != 128:
        raise EdidChecksumError("Invalid EDID length")

    edid = bytearray(edid)
    checksum = (256 - (sum(edid[:-1]) % 256)) % 256
    edid[-1] = checksum
    return bytes(edid)
