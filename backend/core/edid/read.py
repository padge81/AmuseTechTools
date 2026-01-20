import os
from .exceptions import EDIDReadError

EDID_HEADER = b"\x00\xff\xff\xff\xff\xff\xff\x00"
DEFAULT_DRM_PATH = "/sys/class/drm/card0-HDMI-A-1/edid"


def read_edid_drm(path: str = DEFAULT_DRM_PATH) -> bytes:
    if not os.path.exists(path):
        raise EDIDReadError(f"EDID path not found: {path}")

    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 128:
        raise EDIDReadError("EDID too short")

    if not data.startswith(EDID_HEADER):
        raise EDIDReadError("Invalid EDID header")

    return data
