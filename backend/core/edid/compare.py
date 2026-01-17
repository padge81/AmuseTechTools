import hashlib
from pathlib import Path
from typing import Optional, Dict, List

from .checksum import validate_edid
from .exceptions import EDIDError


def edid_hash(edid: bytes) -> str:
    """Return SHA256 hash of EDID bytes."""
    return hashlib.sha256(edid).hexdigest()


def edid_matches(a: bytes, b: bytes) -> bool:
    """Strict byte-for-byte comparison."""
    return a == b


def find_matching_edid(
    edid: bytes,
    directory: str,
):
    """
    Compare EDID against saved .bin files.

    Returns match dict or None.
    """
    if not edid or len(edid) < 128:
        raise EDIDError("EDID data too short to compare")

    base = Path(directory)
    if not base.exists():
        return None

    edid_h = edid_hash(edid)

    for file in sorted(base.glob("*.bin")):
        try:
            data = file.read_bytes()
        except OSError:
            continue

        if data == edid:
            return {
                "filename": file.name,
                "path": str(file),
                "hash": edid_h,
            }

    return None



def list_saved_edids(directory: str) -> List[str]:
    """Return list of saved EDID filenames."""
    base = Path(directory)
    if not base.exists():
        return []
    return sorted(f.name for f in base.glob("*.bin"))
