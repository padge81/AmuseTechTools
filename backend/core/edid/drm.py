from pathlib import Path

def is_connector_connected(connector: str) -> bool:
    if not isinstance(connector, str):
        raise ValueError("connector must be a string")
    """
    Check if DRM connector exists and is connected.
    """
    drm = Path("/sys/class/drm")

    for card in drm.glob("card*-*"):
        if card.name.endswith(connector):
            status = card / "status"
            if status.exists():
                return status.read_text().strip() == "connected"

    return False
