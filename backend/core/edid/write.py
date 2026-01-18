import time
from smbus import SMBus

from .checksum import validate_edid
from .diff import diff_edid
from .exceptions import EDIDWriteError
from .i2c import EDID_I2C_ADDR, find_ddc_i2c_buses, read_edid_i2c


def write_edid_i2c(
    edid: bytes,
    bus: int | None = None,
    verify: bool = True,
    sleep: float = 0.01,
    force: bool = False,
):
    if not force and not validate_edid(edid):
        raise EDIDWriteError("Invalid EDID supplied")

    buses = [bus] if bus is not None else find_ddc_i2c_buses()

    if not buses:
        raise EDIDWriteError("No DDC I2C bus found")

    last_error = None

    for busnum in buses:
        try:
            smb = SMBus(busnum)

            # Write EDID byte-by-byte
            for i, byte in enumerate(edid):
                smb.write_byte_data(EDID_I2C_ADDR, i, byte)
                time.sleep(sleep)

            smb.close()

            # Optional I2C verification
            if verify:
                result = read_edid_i2c(bus=busnum, length=len(edid))
                readback = result["edid"]

                diff = diff_edid(edid, readback)
                if diff:
                    raise EDIDWriteError(
                        f"I2C verification failed on i2c-{busnum}"
                    )

            return {
                "bus": busnum,
                "bytes_written": len(edid),
                "verified": verify,
            }

        except Exception as e:
            last_error = e

    raise EDIDWriteError(f"I2C write failed: {last_error}")
