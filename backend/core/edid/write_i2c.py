def write_edid_for_connector(
    connector: str,
    edid: bytes,
    verify: bool = True,
    sleep: float = 0.01,
    force: bool = False,
):
    bus = resolve_connector_i2c(connector)

    if not force and not validate_edid(edid):
        raise EDIDWriteError("Invalid EDID supplied")

    if len(edid) < 128:
        raise EDIDWriteError("EDID too short")

    try:
        smb = SMBus(bus)

        # Presence check (DDC EEPROM responds)
        smb.read_byte(EDID_I2C_ADDR)

        # Write first EDID block (128 bytes)
        for i, byte in enumerate(edid[:128]):
            smb.write_byte_data(EDID_I2C_ADDR, i, byte)
            time.sleep(sleep)

        smb.close()

        if verify:
            result = read_edid_i2c(
                bus=bus,
                length=128,
                strict=False,
            )

            if diff_edid(edid[:128], result["edid"]):
                raise EDIDWriteError("Verification failed")

        return {
            "connector": connector,
            "bus": bus,
            "bytes_written": 128,
            "verified": verify,
            "forced": force,
        }

    except Exception as e:
        raise EDIDWriteError(str(e))
