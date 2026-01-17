import time
from smbus import SMBus

from .checksum import validate_checksum, validate_edid
from .diff import diff_edid
from .exceptions import EDIDWriteError

EDID_I2C_ADDR = 0x50


def find_ddc_i2c_buses():
    """
    Return a list of likely DDC I2C buses.
    On Pi this is almost always i2c-2, but we probe safely.
    """
    buses = []
    for bus in range(0, 6):
        try:
            smb = SMBus(bus)
            smb.read_byte_data(EDID_I2C_ADDR, 0)
            smb.close()
            buses.append(bus)
        except Exception:
            pass
    return buses


def write_edid_i2c(
    edid: bytes,
    bus: int | None = None,
    verify: bool = True,
    strict: bool = False,
    sleep: float = 0.01,
):
    """
    Write EDID over I2C (DDC).

    strict=False (default):
        - checksum validation only (emulator-safe)

    strict=True:
        - full EDID validation
    """

    # ---- Validation ----
    if strict:
        if not validate_edid(edid):
            raise EDIDWriteError("Strict EDID validation failed")
    else:
        if not validate_checksum(edid):
            raise EDIDWriteError("EDID checksum invalid")

    buses = [bus] if bus is not None else find_ddc_i2c_buses()

    if not buses:
        raise EDIDWriteError("No DDC I2C bus found")

    last_error = None

    for busnum in buses:
        try:
            smb = SMBus(busnum)

            # ---- Write EDID ----
            for i, byte in enumerate(edid):
                smb.write_byte_data(EDID_I2C_ADDR, i, byte)
                time.sleep(sleep)

            # ---- Verify ----
            if verify:
                readback = bytes(
                    smb.read_byte_data(EDID_I2C_ADDR, i)
                    for i in range(len(edid))
                )

                diff = diff_edid(edid, readback)
                if diff:
                    raise EDIDWriteError(
                        f"Verification failed on i2c-{busnum}"
                    )

            smb.close()

            return {
                "bus": busnum,
                "bytes_written": len(edid),
                "verified": verify,
            }

        except Exception as e:
            last_error = e

    raise EDIDWriteError(f"I2C write failed: {last_error}")
