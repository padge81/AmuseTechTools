import hashlib


def edid_hash(edid: bytes) -> str:
    return hashlib.sha256(edid).hexdigest()


def edid_matches(a: bytes, b: bytes) -> bool:
    return a == b
