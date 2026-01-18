import os
from smbus import SMBus

from .checksum import validate_edid
from .exceptions import EDIDWriteError

EDID_I2C_ADDR = 0x50
EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"


def find_ddc_i2c_buses():
    buses = []

    for dev in os.listdir("/dev"):
        if not dev.startswith("i2c-"):
            continue

        try:
            busnum = int(dev.split("-")[1])
            bus = SMBus(busnum)

            header = bytes(
                bus.read_byte_data(EDID_I2C_ADDR, i)
                for i in range(8)
            )

            bus.close()

            if header == EDID_HEADER:
                buses.append(busnum)

        except Exception:
            continue

    return buses


def read_edid_i2c(
    bus: int,
    length: int = 128,
    strict: bool = True,
):
    """
    Read EDID bytes directly from a DDC I2C bus.

    strict=True  -> validate EDID header + checksum
    strict=False -> raw read (used for EEPROM verification)
    """

    try:
        smb = SMBus(bus)
        edid = bytes(
            smb.read_byte_data(EDID_I2C_ADDR, i)
            for i in range(length)
        )
        smb.close()
    except Exception as e:
        raise EDIDWriteError(
            f"I2C EDID read failed on i2c-{bus}: {e}"
        )

    if strict and not validate_edid(edid):
        raise EDIDWriteError(
            f"Invalid EDID read from i2c-{bus}"
        )

    return {
        "bus": bus,
        "edid": edid,
        "length": len(edid),
        "strict": strict,
    }
