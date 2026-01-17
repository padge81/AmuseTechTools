import os

from .exceptions import EDIDWriteError
from .checksum import validate_edid


def write_edid_i2c(
    edid: bytes,
    bus: int | None = None,
    verify: bool = True,
    sleep: float = 0.01,
):
    if not validate_edid(edid):
        raise EDIDWriteError("Invalid EDID")

    buses = [bus] if bus is not None else find_ddc_i2c_buses()

    if not buses:
        raise EDIDWriteError("No DDC I2C bus found")

    last_error = None

    for busnum in buses:
        try:
            smb = SMBus(busnum)

            # Write EDID
            for i, byte in enumerate(edid):
                smb.write_byte_data(EDID_I2C_ADDR, i, byte)
                time.sleep(sleep)

            if verify:
                readback = bytes(
                    smb.read_byte_data(EDID_I2C_ADDR, i)
                    for i in range(len(edid))
                )

                diff = diff_edid(edid, readback)
                if diff:
                    raise EDIDWriteError(f"Verification failed on i2c-{busnum}")

            smb.close()
            return {
                "bus": busnum,
                "bytes_written": len(edid),
                "verified": verify,
                "diff": None,
            }

        except Exception as e:
            last_error = e

    raise EDIDWriteError(f"I2C write failed: {last_error}")
