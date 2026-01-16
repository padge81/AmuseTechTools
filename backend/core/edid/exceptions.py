class EDIDError(Exception):
    """Base class for all EDID-related errors."""
    pass


class EDIDReadError(EDIDError):
    """Raised when EDID reading fails."""
    pass


class EDIDWriteError(EDIDError):
    """Raised when EDID writing fails."""
    pass


class EDIDChecksumError(EDIDError):
    """Raised when EDID checksum validation fails."""
    pass