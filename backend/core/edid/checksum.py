from .exceptions import EDIDChecksumError


def validate_checksum(block: bytes) -> bool:
    return sum(block) & 0xFF == 0


def validate_edid(edid: bytes) -> None:
    if not validate_checksum(edid[:128]):
        raise EDIDChecksumError("Base EDID checksum invalid")

    ext_count = edid[126]
    for i in range(ext_count):
        block = edid[128 + i*128 : 256 + i*128]
        if not validate_checksum(block):
            raise EDIDChecksumError(f"Extension block {i} checksum invalid")
