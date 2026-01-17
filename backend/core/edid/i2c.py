import os
import time
from smbus import SMBus

from .checksum import validate_edid
from .diff import diff_edid
from .exceptions import EDIDWriteError

EDID_I2C_ADDR = 0x50
EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"


def find_ddc_i2c_buses():
    buses = []

    for dev in os.listdir("/dev"):
        if not dev.startswith("i2c-"):
            continue

        busnum = int(dev.split("-")[1])
        try:
            bus = SMBus(busnum)
            data = bytes(bus.read_byte_data(EDID_I2C_ADDR, i) for i in range(8))
            bus.close()

            if data == EDID_HEADER:
                buses.append(busnum)

        except Exception:
            continue

    return buses
