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
    """
    Write EDID to a DDC I2C bus.

    force=True bypasses strict EDID validation (for emulators/adapters).
    """

    if not force:
        if not validate_edid(edid):
            raise EDIDWriteError("Invalid EDID supplied")
    else:
        # Still require minimum size sanity
        if len(edid) < 128:
            raise EDIDWriteError("EDID too short to write")

    buses = [bus] if bus is not None else find_ddc_i2c_buses()

    if not buses:
        raise EDIDWriteError("No DDC I2C bus found")

    last_error = None

    for busnum in buses:
        try:
            smb = SMBus(busnum)

            # Write EDID byte-by-byte (safe for EEPROMs)
            for i, byte in enumerate(edid):
                smb.write_byte_data(EDID_I2C_ADDR, i, byte)
                time.sleep(sleep)

            smb.close()

            # Optional I2C verification
            if verify:
                result = read_edid_i2c(
                    bus=busnum,
                    length=len(edid),
                    strict=False,  # IMPORTANT: EEPROM may not checksum yet
                )
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
                "forced": force,
            }

        except Exception as e:
            last_error = e

    raise EDIDWriteError(f"I2C write failed: {last_error}")
