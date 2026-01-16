from backend.core.edid import read_edid_drm, find_matching_edid

EDID_DIR = "edid_files"


def main():
    print("Reading EDID...")
    edid = read_edid_drm()

    print("Checking saved EDIDs...")
    match = find_matching_edid(edid, EDID_DIR)

    if match:
        print(f"✔ MATCH FOUND: {match}")
    else:
        print("✖ NO MATCH FOUND")


if __name__ == "__main__":
    main()
