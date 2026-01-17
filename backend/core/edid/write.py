import os
import time
from typing import Optional, Dict, Any

from smbus import SMBus

from .checksum import validate_edid
from .diff import diff_edid
from .exceptions import EDIDWriteError

# EDID / DDC constants
EDID_I2C_ADDR = 0x50
EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"


def find_ddc_i2c_buses() -> list[int]:
    """
    Scan /dev/i2c-* for devices responding with a valid EDID header
    at address 0x50.
    """
    buses: list[int] = []

    for dev in os.listdir("/dev"):
        if not dev.startswith("i2c-"):
            continue

        try:
            busnum = int(dev.split("-")[1])
            smb = SMBus(busnum)

            header = bytes(
                smb.read_byte_data(EDID_I2C_ADDR, i)
                for i in range(8)
            )

            smb.close()

            if header == EDID_HEADER:
                buses.append(busnum)

        except Exception:
            continue

    return buses


def write_edid_i2c(
    edid: bytes,
    bus: Optional[int] = None,
    verify: bool = True,
    sleep: float = 0.01,
) -> Dict[str, Any]:
    """
    Write EDID to a DDC I2C EEPROM (EDID emulator).

    If bus is None, all detected DDC buses are tried until success.
    """

    # --- Validation ---
    if not validate_edid(edid):
        raise EDIDWriteError("Invalid EDID supplied")

    # --- Bus selection ---
    buses = [bus] if bus is not None else find_ddc_i2c_buses()

    if not buses:
        raise EDIDWriteError("No DDC I2C buses found")

    last_error: Exception | None = None

    # --- Attempt write on each bus ---
    for busnum in buses:
        try:
            smb = SMBus(busnum)

            # Write EDID byte-by-byte
            for offset, value in enumerate(edid):
                smb.write_byte_data(EDID_I2C_ADDR, offset, value)
                time.sleep(sleep)

            # --- Verification ---
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
                "diff": None,
            }

        except Exception as e:
            last_error = e
            try:
                smb.close()
            except Exception:
                pass

    raise EDIDWriteError(f"I2C EDID write failed: {last_error}")
