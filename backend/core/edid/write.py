import time
from smbus import SMBus

from .checksum import validate_edid
from .diff import diff_edid
from .exceptions import EDIDWriteError
from .i2c import EDID_I2C_ADDR, find_ddc_i2c_buses, read_edid_i2c


def write_edid_i2c(
    edid: bytes,
    bus: int,
    verify: bool = True,
    sleep: float = 0.01,
    force: bool = False,
):
    if bus is None:
        raise EDIDWriteError("Explicit I2C bus required")

    if not force and not validate_edid(edid):
        raise EDIDWriteError("Invalid EDID supplied")

    if len(edid) < 128:
        raise EDIDWriteError("EDID too short")

    try:
        smb = SMBus(bus)          # ← OPEN BUS HERE
        try:
            # Presence check
            smb.read_byte(EDID_I2C_ADDR)

            for i, byte in enumerate(edid[:128]):
                smb.write_byte_data(EDID_I2C_ADDR, i, byte)
                time.sleep(sleep)

        finally:
            smb.close()           # ← CLOSE BUS **HERE** (ALWAYS)

        if verify:
            result = read_edid_i2c(
                bus=bus,
                length=128,
                strict=False
            )
            if diff_edid(edid[:128], result["edid"]):
                raise EDIDWriteError("Verification failed")

        return {
            "bus": bus,
            "bytes_written": 128
        }

    except Exception as e:
        raise EDIDWriteError(str(e))

