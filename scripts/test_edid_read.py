#!/usr/bin/env python3

import sys
from backend.core.edid import (
    read_edid_drm,
    validate_edid,
    decode_basic,
    edid_to_hex,
    edid_hash,
    diff_edid,
    EDIDError,
)

DRM_PATH = "/sys/class/drm/card0-HDMI-A-1/edid"


def banner(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    try:
        banner("READ EDID")
        edid = read_edid_drm(DRM_PATH)
        print(f"EDID length: {len(edid)} bytes")

        banner("CHECKSUM VALIDATION")
        validate_edid(edid)
        print("✔ Checksum OK")

        banner("DECODE BASIC INFO")
        info = decode_basic(edid)
        for k, v in info.items():
            print(f"{k:15}: {v}")

        banner("HEX DUMP (first 128 bytes)")
        print(edid_to_hex(edid[:128]))

        banner("HASH")
        h = edid_hash(edid)
        print(h)

        banner("SELF DIFF TEST")
        diff = diff_edid(edid, edid)
        print("✔ Diff empty" if not diff else diff)


        diff = diff_edid(edid, edid)
        print("✔ Diff empty" if not diff else diff)

        banner("ALL TESTS PASSED")
        return 0

    except EDIDError as e:
        print(f"❌ EDID ERROR: {e}")
        return 1

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
