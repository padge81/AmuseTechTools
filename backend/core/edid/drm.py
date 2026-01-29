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
    
def list_connectors():
    """
    Enumerate DRM connectors from /sys/class/drm.
    Returns a list of dicts with basic connector info.
    """
    connectors = []
    drm = Path("/sys/class/drm")

    for card in drm.glob("card*-*"):
        status_file = card / "status"
        if not status_file.exists():
            continue

        name = card.name.split("-", 1)[1]  # HDMI-A-1
        status = status_file.read_text().strip()

        connectors.append({
            "name": name,
            "connected": status == "connected",
            "sysfs_path": str(card),
        })

    return connectors