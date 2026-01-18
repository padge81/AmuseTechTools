#!/usr/bin/env python3

import sys
from pathlib import Path

from backend.core.edid.checksum import validate_edid
from backend.core.edid.diff import diff_edid
from backend.core.edid.write import write_edid_i2c
from backend.core.edid.i2c import read_edid_i2c
from backend.core.edid.exceptions import EDIDWriteError

EDID_FILE = Path("edid_files/UNIS3EDID.bin")


def banner(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    try:
        banner("LOAD EDID FILE")

        edid = EDID_FILE.read_bytes()
        print(f"File EDID length: {len(edid)} bytes")

        if validate_edid(edid):
            print("✔ File EDID valid")
            force = False
        else:
            print("⚠ File EDID failed strict validation — forcing write")
            force = True

        banner("WRITE EDID TO I2C (DDC)")

        result = write_edid_i2c(
            edid,
            verify=False,
            force=force,
        )

        bus = result["bus"]
        print(f"✔ Written to i2c-{bus}")
        print(f"✔ Bytes written: {result['bytes_written']}")

        banner("READ BACK EDID FROM I2C")

        readback = read_edid_i2c(
            bus=bus,
            length=len(edid),
            strict=False,   # ← THIS IS THE KEY
        )

        rb_edid = readback["edid"]
        print(f"Readback length: {len(rb_edid)} bytes")

        banner("VERIFY WRITTEN EDID (I2C)")

        diff = diff_edid(edid, rb_edid)
        if diff:
            print("❌ I2C EDID mismatch detected:")
            for line in diff:
                print(line)
            sys.exit(1)

        print("✔ I2C EDID verified successfully")

        banner("WRITE TEST COMPLETE")
        return 0

    except EDIDWriteError as e:
        print(f"\n❌ EDID ERROR: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
