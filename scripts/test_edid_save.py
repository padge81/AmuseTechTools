from backend.core.edid import read_edid_drm, save_edid

EDID_DIR = "edid_files"


def main():
    edid = read_edid_drm()

    print("Saving EDID...")
    path = save_edid(
        edid,
        name="My HDMI Display 1080p",
        directory=EDID_DIR,
    )

    print(f"✔ Saved to {path}")


if __name__ == "__main__":
    main()
