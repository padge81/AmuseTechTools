import hashlib
from pathlib import Path


def hash_edid(edid: bytes) -> str:
    return hashlib.sha256(edid).hexdigest()


def find_match(edid: bytes, directory: Path) -> str | None:
    target = hash_edid(edid)

    for f in directory.glob("*.bin"):
        if hash_edid(f.read_bytes()) == target:
            return f.name

    return None
