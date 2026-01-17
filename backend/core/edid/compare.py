import hashlib
from pathlib import Path
from .exceptions import EDIDError


def edid_hash(edid: bytes) -> str:
    return hashlib.sha256(edid).hexdigest()


def find_matching_edid(edid: bytes, directory: str):
    """
    Return a list of exact EDID matches in directory.
    """
    if not edid or len(edid) < 128:
        raise EDIDError("Invalid EDID supplied for comparison")

    base = Path(directory)
    if not base.exists():
        return []

    matches = []
    target_hash = edid_hash(edid)

    for file in sorted(base.glob("*.bin")):
        try:
            data = file.read_bytes()
        except OSError:
            continue

        if data == edid:
            matches.append({
                "filename": file.name,
                "path": str(file),
                "exact": True,
                "hash": target_hash,
            })

    return matches
