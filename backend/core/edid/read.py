import os
from .exceptions import EDIDReadError

EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"
DRM_BASE_PATH = "/sys/class/drm"


def find_drm_edid_paths() -> list[str]:
    """
    Returns a list of valid DRM EDID file paths.
    Example:
      /sys/class/drm/card0-HDMI-A-1/edid
      /sys/class/drm/card0-HDMI-A-2/edid
    """
    paths = []

    if not os.path.exists(DRM_BASE_PATH):
        return paths

    for entry in os.listdir(DRM_BASE_PATH):
        if "HDMI" not in entry:
            continue

        edid_path = os.path.join(DRM_BASE_PATH, entry, "edid")
        if os.path.exists(edid_path):
            paths.append(edid_path)

    return paths


def read_edid_drm(path: str | None = None) -> bytes:
    """
    Read EDID from a DRM connector.
    If no path is provided, auto-detect the first available HDMI EDID.
    """

    if path is None:
        paths = find_drm_edid_paths()
        if not paths:
            raise EDIDReadError("No HDMI EDID devices found")
        path = paths[0]

    if not os.path.exists(path):
        raise EDIDReadError(f"EDID path not found: {path}")

    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 128:
        raise EDIDReadError("EDID too short")

    if not data.startswith(EDID_HEADER):
        raise EDIDReadError("Invalid EDID header")

    return data

