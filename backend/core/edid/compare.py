import os
import hashlib
from typing import Optional


def edid_hash(edid: bytes) -> str:
    return hashlib.sha256(edid).hexdigest()


def edid_matches(a: bytes, b: bytes) -> bool:
    return a == b


def find_matching_edid(
    edid: bytes,
    edid_dir: str
) -> Optional[str]:
    """
    Compare EDID bytes against all .bin files in edid_dir.

    Returns:
        filename if match found, else None
    """
    if not os.path.isdir(edid_dir):
        return None

    for fname in sorted(os.listdir(edid_dir)):
        if not fname.lower().endswith(".bin"):
            continue

        path = os.path.join(edid_dir, fname)

        try:
            with open(path, "rb") as f:
                stored = f.read()
        except Exception:
            continue

        if edid_matches(edid, stored):
            return fname

    return None
