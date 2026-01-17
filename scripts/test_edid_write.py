#!/usr/bin/env python3

import sys
import os

from backend.core.edid import (
    read_edid_drm,
    validate_edid,
    edid_to_hex,
    diff_edid,
    write_edid,
    EDIDError,
)

# DRM connector (NOT the edid file)
CONNECTOR_PATH = "/sys/class/drm/card0-HDMI-A-1"

# Path to EDID binary to write
EDID_FILE = "./edid_files/UNIS3EDID.bin"   # CHANGE IF NEEDED


def banner(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    try:
        if not os.path.exists(EDID_FILE):
            print(f"❌ File not found: {EDID_FILE}")
            return 1

        banner("LOAD EDID FILE")
        with open(EDID_FILE, "rb") as f:
            file_edid = f.read()

        print(f"File EDID length: {len(file_edid)} bytes")
        validate_edid(file_edid)
        print("✔ File EDID valid")

        banner("WRITE EDID TO DRM CONNECTOR")
        written = write_edid(
            edid=file_edid,
            connector_path=CONNECTOR_PATH,
            strict=True,
        )
        print(f"✔ write_edid wrote {len(written)} bytes")

        banner("READ BACK EDID FROM DRM")
        readback = read_edid_drm(os.path.join(CONNECTOR_PATH, "edid"))
        print(f"Readback length: {len(readback)} bytes")

        banner("VERIFY WRITTEN EDID")
        diff = diff_edid(file_edid, readback)

        if not diff:
            print("✔ EDID verified (exact match)")
        else:
            print("⚠ EDID differs:")
            print(diff)

        banner("HEX DUMP (first 128 bytes)")
        print(edid_to_hex(readback[:128]))

        banner("WRITE TEST COMPLETE")
        return 0

    except EDIDError as e:
        print(f"❌ EDID ERROR: {e}")
        return 1

    except PermissionError:
        print("❌ Permission denied (needs sudo)")
        return 1

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
