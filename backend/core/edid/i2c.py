from smbus2 import SMBus
from .exceptions import EdidReadError, EdidWriteError

EDID_I2C_ADDR = 0x50
EDID_LENGTH = 128


def read_block(bus_num: int) -> bytes:
    try:
        with SMBus(bus_num) as bus:
            data = bus.read_i2c_block_data(EDID_I2C_ADDR, 0, EDID_LENGTH)
            return bytes(data)
    except Exception as e:
        raise EdidReadError(str(e))


def write_block(bus_num: int, data: bytes):
    if len(data) != EDID_LENGTH:
        raise EdidWriteError("EDID must be exactly 128 bytes")

    try:
        with SMBus(bus_num) as bus:
            for offset in range(0, EDID_LENGTH, 16):
                chunk = list(data[offset:offset + 16])
                bus.write_i2c_block_data(
                    EDID_I2C_ADDR,
                    offset,
                    chunk
                )
    except Exception as e:
        raise EdidWriteError(str(e))
