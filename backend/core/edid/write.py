import os

from .exceptions import EDIDWriteError
from .checksum import validate_edid


def write_edid(
    edid: bytes,
    connector_path: str,
    strict: bool = True,
) -> bytes:
    """
    Write EDID to a DRM connector override.

    connector_path example:
        /sys/class/drm/card0-HDMI-A-1
    """

    if strict:
        validate_edid(edid)

    override_path = os.path.join(connector_path, "edid_override")

    if not os.path.exists(override_path):
        raise EDIDWriteError(
            f"EDID override not supported on {connector_path}"
        )

    try:
        with open(override_path, "wb") as f:
            f.write(edid)
    except PermissionError:
        raise EDIDWriteError("Permission denied (need sudo)")
    except OSError as e:
        raise EDIDWriteError(f"Failed to write EDID: {e}") from e

    return edid
