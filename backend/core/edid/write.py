from .i2c import write_block, read_block
from .checksum import fix_checksum
from .diff import diff_edid


def write_edid(bus_num: int, edid: bytes) -> dict:
    fixed = fix_checksum(edid)
    write_block(bus_num, fixed)

    verify = read_block(bus_num)
    verified = verify == fixed

    return {
        "verified": verified,
        "diff": "" if verified else diff_edid(fixed, verify)
    }
