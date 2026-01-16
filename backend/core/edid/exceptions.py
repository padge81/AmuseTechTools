class EdidError(Exception):
    pass


class EdidReadError(EdidError):
    pass


class EdidWriteError(EdidError):
    pass


class EdidChecksumError(EdidError):
    pass
