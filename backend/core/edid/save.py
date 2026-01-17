import os
import re
from typing import Optional

from .checksum import validate_checksum, validate_edid
from .compare import find_matching_edid
from .exceptions import EDIDWriteError


_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_filename(name: str) -> str:
    """
    Convert user input into a safe filename.
    """
    name = name.strip().lower()
    name = name.replace(" ", "_")
    name = _SAFE_NAME_RE.sub("", name)
    return name or "edid"


def ensure_bin_extension(name: str) -> str:
    if not name.endswith(".bin"):
        return f"{name}.bin"
    return name


def save_edid(
    edid: bytes,
    name: str,
    directory: str,
    overwrite: bool = False,
    strict: bool = False,
) -> str:
    # ---- Validate EDID ----
    if strict:
        if not validate_edid(edid):
            raise EDIDWriteError("EDID failed strict validation")
    else:
        if not validate_checksum(edid):
            raise EDIDWriteError("EDID checksum invalid")

    # ---- Ensure directory exists ----
    os.makedirs(directory, exist_ok=True)

    # ---- Content-based duplicate check ----
    matches = find_matching_edid(edid, directory)
    if matches:
        existing = matches[0]["filename"]
        raise EDIDWriteError(
            f"EDID already exists (content match): {existing}"
        )

    # ---- Filename handling ----
    safe = sanitize_filename(name)
    filename = ensure_bin_extension(safe)
    path = os.path.join(directory, filename)

    if os.path.exists(path) and not overwrite:
        raise EDIDWriteError(f"Filename already exists: {filename}")

    # ---- Write file ----
    try:
        with open(path, "wb") as f:
            f.write(edid)
    except OSError as e:
        raise EDIDWriteError(f"Failed to write EDID: {e}") from e

    return path
