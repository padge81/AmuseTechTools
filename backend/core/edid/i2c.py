from smbus2 import SMBus

EDID_I2C_ADDR = 0x50


def i2c_read(bus: int, offset: int, length: int = 16) -> bytes:
    with SMBus(bus) as b:
        b.write_byte(EDID_I2C_ADDR, offset)
        return bytes(b.read_byte(EDID_I2C_ADDR) for _ in range(length))
