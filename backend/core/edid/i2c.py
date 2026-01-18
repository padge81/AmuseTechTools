def read_edid_i2c(
    bus: int,
    length: int = 128,
    strict: bool = False,
):
    try:
        smb = SMBus(bus)

        data = bytes(
            smb.read_byte_data(EDID_I2C_ADDR, i)
            for i in range(length)
        )

        smb.close()

        if strict and not validate_edid(data):
            raise EDIDWriteError(
                f"Invalid EDID read from i2c-{bus}"
            )

        return {
            "bus": bus,
            "edid": data,
            "valid": validate_edid(data),
        }

    except Exception as e:
        raise EDIDWriteError(
            f"I2C EDID read failed on i2c-{bus}: {e}"
        ) from e
