import os
import hashlib
from typing import Optional, Tuple, List


def edid_hash(edid: bytes) -> str:
    return hashlib.sha256(edid).hexdigest()


def edid_matches(a: bytes, b: bytes) -> bool:
    return a == b


def find_matching_edid(
    edid: bytes,
    edid_dir: str
) -> Optional[str]:
    """
    Compare EDID bytes against saved .bin files.

    Returns:
        filename (str) if match found
        None if no match
    """
    if not os.path.isdir(edid_dir):
        return None

    live_hash = edid_hash(edid)

    for fname in sorted(os.listdir(edid_dir)):
        if not fname.lower().endswith(".bin"):
            continue

        path = os.path.join(edid_dir, fname)

        try:
            with open(path, "rb") as f:
                saved = f.read()
        except OSError:
            continue

        if len(saved) < 128:
            continue

        # Fast hash compare
        if edid_hash(saved) != live_hash:
            continue

        # Absolute safety: byte-for-byte compare
        if edid_matches(edid, saved):
            return fname

    return None
