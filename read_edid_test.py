#!/usr/bin/env python3
from smbus2 import SMBus, i2c_msg

EDID_I2C_ADDR = 0x50
EDID_LENGTH = 128
I2C_BUS = 2   # default on Pi for HDMI EDID (change if needed)

def read_edid(bus_num=I2C_BUS):
    data = bytearray()

    with SMBus(bus_num) as bus:
        # EDID is read in 16-byte blocks
        for offset in range(0, EDID_LENGTH, 16):
            write = i2c_msg.write(EDID_I2C_ADDR, [offset])
            read = i2c_msg.read(EDID_I2C_ADDR, 16)
            bus.i2c_rdwr(write, read)
            data.extend(read)

    return bytes(data)

def hexdump(data):
    for i in range(0, len(data), 16):
        row = data[i:i+16]
        print(f"{i:02X}: " + " ".join(f"{b:02X}" for b in row))

if __name__ == "__main__":
    try:
        edid = read_edid()
        print("EDID read OK\n")
        hexdump(edid)

        # Quick sanity check
        if edid[:8] == b"\x00\xff\xff\xff\xff\xff\xff\x00":
            print("\nValid EDID header detected ✔")
        else:
            print("\nWARNING: Invalid EDID header ✖")

    except Exception as e:
        print("EDID read FAILED")
        print(e)
