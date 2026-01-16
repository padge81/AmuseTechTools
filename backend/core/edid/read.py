import base64
from .i2c import read_block
from .checksum import checksum_is_valid
from .decode import decode_edid


def read_edid(bus_num: int) -> dict:
    raw = read_block(bus_num)

    return {
        "binary": raw,
        "binary_b64": base64.b64encode(raw).decode(),
        "checksum_valid": checksum_is_valid(raw),
        "decoded": decode_edid(raw)
    }
