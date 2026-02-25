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
    
from pathlib import Path

def list_connectors():
    """
    Enumerate DRM connectors from /sys/class/drm.
    Returns connector info including EDID presence and path.
    """
    connectors = []
    drm = Path("/sys/class/drm")

    for card in drm.glob("card*-*"):
        status_file = card / "status"
        if not status_file.exists():
            continue

        name = card.name.split("-", 1)[1]  # HDMI-A-1
        status = status_file.read_text().strip()

        edid_file = card / "edid"
        edid_present = edid_file.exists() and edid_file.stat().st_size > 0

        connector_id_file = card / "connector_id"
        connector_id = None
        if connector_id_file.exists():
            try:
                connector_id = int(connector_id_file.read_text().strip())
            except ValueError:
                connector_id = None

        connectors.append({
            "name": name,
            "connector_id": connector_id,
            "connected": status == "connected",
            "sysfs_path": str(card),
            "edid_present": edid_present,
            "edid_path": str(edid_file) if edid_present else None,
        })

    return sorted(connectors, key=lambda c: c["name"])
