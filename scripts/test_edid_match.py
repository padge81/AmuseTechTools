from backend.core.edid import (
    read_edid_drm,
    find_matching_edid,
)

EDID_DIR = "edid_files"


def main():
    edid = read_edid_drm()

    matches = find_matching_edid(edid, EDID_DIR)

    if not matches:
        print("✖ No matching EDID found")
        return

    print("✔ Matching EDIDs:")
    for m in matches:
        print(f" - {m['filename']} (exact={m['exact']})")


if __name__ == "__main__":
    main()
