def read_edid_i2c(
    bus: int | None = None,
    length: int = 128,
    validate: bool = True,
):
    """
    Read EDID directly from DDC over I2C (0x50)

    Returns:
        dict with keys:
            bus
            edid (bytes)
            length
            valid
    """
    buses = [bus] if bus is not None else find_ddc_i2c_buses()

    if not buses:
        raise EDIDWriteError("No DDC I2C bus found")

    last_error = None

    for busnum in buses:
        try:
            smb = SMBus(busnum)

            data = bytes(
                smb.read_byte_data(EDID_I2C_ADDR, i)
                for i in range(length)
            )

            smb.close()

            # Header sanity check
            if not data.startswith(EDID_HEADER):
                raise EDIDWriteError(
                    f"Invalid EDID header on i2c-{busnum}"
                )

            is_valid = validate_edid(data) if validate else True

            if validate and not is_valid:
                raise EDIDWriteError(
                    f"Invalid EDID checksum on i2c-{busnum}"
                )

            return {
                "bus": busnum,
                "edid": data,
                "length": len(data),
                "valid": is_valid,
            }

        except Exception as e:
            last_error = e

    raise EDIDWriteError(f"I2C EDID read failed: {last_error}")

