from .exceptions import EDIDWriteError


def write_edid(edid: bytes, port: int):
    raise EDIDWriteError(
        "EDID writing is only supported for approved emulators"
    )
