import sys
from pathlib import Path

from backend.core.edid.checksum import validate_edid
from backend.core.edid.diff import diff_edid
from backend.core.edid.write import write_edid_i2c
from backend.core.edid.i2c import read_edid_i2c
from backend.core.edid.exceptions import EDIDWriteError


EDID_FILE = Path("edid_files/UNIS3EDID.bin")
DRM_CONNECTOR = "card0-HDMI-A-1"


def main():
    try:
        print("=" * 60)
        print("LOAD EDID FILE")
        print("=" * 60)

        edid = EDID_FILE.read_bytes()
        print(f"File EDID length: {len(edid)} bytes")

        if not validate_edid(edid):
            raise EDIDWriteError("File EDID invalid")

        print("✔ File EDID valid")

        print("\n" + "=" * 60)
        print("WRITE EDID TO I2C (DDC)")
        print("=" * 60)

        result = write_edid_i2c(edid, verify=False)
        bus = result["bus"]

        print(f"✔ Written to i2c-{bus}")
        print(f"✔ Bytes written: {result['bytes_written']}")

        print("\n" + "=" * 60)
        print("READ BACK EDID FROM I2C")
        print("=" * 60)

        readback = read_edid_i2c(bus=bus, length=len(edid))
        rb_edid = readback["edid"]

        print(f"Readback length: {len(rb_edid)} bytes")

        print("\n" + "=" * 60)
        print("VERIFY WRITTEN EDID (I2C)")
        print("=" * 60)

        diff = diff_edid(edid, rb_edid)
        if diff:
            print("❌ I2C EDID mismatch detected:")
            for line in diff:
                print(line)
            sys.exit(1)

        print("✔ I2C EDID verified successfully")

        print("\n" + "=" * 60)
        print("OPTIONAL: READ DRM EDID (INFO ONLY)")
        print("=" * 60)

        try:
            drm_edid = read_edid_drm(DRM_CONNECTOR)
            if drm_edid:
                print(f"DRM EDID length: {len(drm_edid)} bytes")
                print("⚠ DRM EDID may differ due to kernel caching")
        except Exception as e:
            print(f"⚠ DRM read skipped: {e}")

        print("\n" + "=" * 60)
        print("WRITE TEST COMPLETE")
        print("=" * 60)

    except EDIDWriteError as e:
        print(f"\n❌ EDID ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
