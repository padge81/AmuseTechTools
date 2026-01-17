import os
import time
from smbus import SMBus

from .checksum import validate_edid
from .exceptions import EDIDReadError

EDID_I2C_ADDR = 0x50
EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"


def find_ddc_i2c_buses():
    """
    Scan /dev/i2c-* and return buses that respond with a valid EDID header.
    """
    buses = []

    for dev in sorted(os.listdir("/dev")):
        if not dev.startswith("i2c-"):
            continue

        try:
            busnum = int(dev.split("-")[1])
            smb = SMBus(busnum)

            data = bytes(
                smb.read_byte_data(EDID_I2C_ADDR, i)
                for i in range(len(EDID_HEADER))
            )

            smb.close()

            if data == EDID_HEADER:
                buses.append(busnum)

        except Exception:
            continue

    return buses


def read_edid_i2c(
    bus: int | None = None,
    length: int = 128,
    validate: bool = True,
    sleep: float = 0.005,
):
    """
    Read EDID directly from DDC via I2C.

    Returns:
        {
            "bus": bus number,
            "edid": bytes,
        }
    """
    buses = [bus] if bus is not None else find_ddc_i2c_buses()

    if not buses:
        raise EDIDReadError("No DDC I2C bus found")

    last_error = None

    for busnum in buses:
        try:
            smb = SMBus(busnum)

            edid = bytearray()
            for i in range(length):
                edid.append(smb.read_byte_data(EDID_I2C_ADDR, i))
                time.sleep(sleep)

            smb.close()

            edid = bytes(edid)

            if validate and not validate_edid(edid):
                raise EDIDReadError(f"Invalid EDID read from i2c-{busnum}")

            return {
                "bus": busnum,
                "edid": edid,
            }

        except Exception as e:
            last_error = e

    raise EDIDReadError(f"I2C EDID read failed: {last_error}")
