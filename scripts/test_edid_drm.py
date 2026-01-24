#!/usr/bin/env python3

from pathlib import Path

from backend.core.edid.write_i2c import write_edid_for_connector
from backend.core.edid.checksum import validate_edid
from backend.core.edid.exceptions import EDIDWriteError

EDID_FILE = Path("edid_files/HDMI_EDID_Emulator.bin")


def main():
    try:
        edid = EDID_FILE.read_bytes()
        print(f"Loaded EDID: {len(edid)} bytes")

        if validate_edid(edid):
            print("✔ EDID valid")
            force = False
        else:
            print("⚠ EDID invalid — forcing write")
            force = True

        result = write_edid_for_connector(
            connector="HDMI-A-1",
            edid=edid,
            verify=False,
            force=force,
        )

        print("✔ Write successful")
        print(result)

    except EDIDWriteError as e:
        print(f"❌ EDID ERROR: {e}")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


if __name__ == "__main__":
    main()
