#!/usr/bin/env python3

import sys
import os

from backend.core.edid.i2c import read_edid_i2c
from backend.core.edid import (
    read_edid_drm,
    write_edid_i2c,
    validate_edid,
    edid_to_hex,
    diff_edid,
    EDIDError,
)

# ---- CONFIG ----
DRM_PATH = "/sys/class/drm/card0-HDMI-A-1/edid"
EDID_FILE = "./edid_files/UNIS3EDID.bin"   # CHANGE IF NEEDED


def banner(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> int:
    try:
        # ---- Load EDID file ----
        banner("LOAD EDID FILE")

        if not os.path.exists(EDID_FILE):
            print(f"❌ File not found: {EDID_FILE}")
            return 1

        with open(EDID_FILE, "rb") as f:
            file_edid = f.read()

        print(f"File EDID length: {len(file_edid)} bytes")
        validate_edid(file_edid)
        print("✔ File EDID valid")

        # ---- Write EDID ----
        banner("WRITE EDID TO I2C (DDC)")

        result = write_edid_i2c(
            edid=file_edid,
            bus=None,          # auto-detect
            verify=True,
            sleep=0.01,
        )

        print(f"✔ Written to i2c-{result['bus']}")
        print(f"✔ Bytes written: {result['bytes_written']}")

        banner("READ BACK EDID FROM I2C")
        readback = read_edid_i2c(bus=2)

        readback = read_edid_drm(DRM_PATH)
        print(f"Readback length: {len(readback)} bytes")

        # ---- Verify ----
        banner("VERIFY WRITTEN EDID")

        diff = diff_edid(file_edid, readback)

        if not diff:
            print("✔ EDID verified (exact match)")
        else:
            print("⚠ EDID mismatch detected:")
            print(diff)

        # ---- Display ----
        banner("HEX DUMP (FIRST 128 BYTES)")
        print(edid_to_hex(readback[:128]))

        banner("WRITE TEST COMPLETE")
        return 0

    except EDIDError as e:
        print(f"❌ EDID ERROR: {e}")
        return 1

    except PermissionError:
        print("❌ Permission denied (run with sudo)")
        return 1

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
