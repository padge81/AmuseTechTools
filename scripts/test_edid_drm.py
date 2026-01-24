from backend.core.edid.write_i2c import write_edid_for_connector, edid

result = write_edid_for_connector(
    connector="HDMI-A-1",
    edid=edid,
    verify=False,
    force=force,
)

print(result)
