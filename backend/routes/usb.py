from flask import Blueprint, jsonify, request
from pathlib import Path

# -------------------------------------------------
# Configuration
# -------------------------------------------------

USB_MOUNT_BASES = ["/media", "/mnt"]

# EDID storage directory (same one used elsewhere)
EDID_DIR = Path("edid_files")

bp = Blueprint("usb", __name__, url_prefix="/usb")


# -------------------------------------------------
# LIST USB DRIVES
# -------------------------------------------------

@bp.route("/drives")
def list_drives():
    drives = []

    for base in USB_MOUNT_BASES:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for mount in base_path.iterdir():
            if mount.is_dir():
                drives.append(str(mount))

    return jsonify(drives)

# -------------------------------------------------
# IMPORT EDIDS FROM USB
# -------------------------------------------------

@bp.route("/import", methods=["POST"])
def import_edids():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No request data"}), 400

    drive = Path(data.get("drive", ""))

    if not drive.exists() or not drive.is_dir():
        return jsonify({"error": "Drive not found"}), 400

    if not EDID_DIR.exists():
        EDID_DIR.mkdir(parents=True, exist_ok=True)

    imported = []
    skipped = []

    # Cache local EDIDs for fast comparison
    local_edids = []
    for file in EDID_DIR.rglob("*.bin"):
        try:
            local_edids.append(file.read_bytes())
        except OSError:
            pass

    # Scan USB for .bin files
    for usb_file in drive.glob("*.bin"):
        try:
            usb_edid = usb_file.read_bytes()
        except OSError:
            skipped.append(usb_file.name)
            continue

        # Exact byte-for-byte comparison
        if usb_edid in local_edids:
            skipped.append(usb_file.name)
            continue

        target = EDID_DIR / usb_file.name

        # Avoid overwrite even if name matches but content differs
        if target.exists():
            skipped.append(usb_file.name)
            continue

        target.write_bytes(usb_edid)
        imported.append(usb_file.name)

    return jsonify({
        "imported": imported,
        "skipped": skipped
    })

# -------------------------------------------------
# EXPORT EDIDS TO USB
# -------------------------------------------------

@bp.route("/export", methods=["POST"])
def export_edids():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No request data"}), 400

    drive = Path(data.get("drive", ""))

    if not drive.exists() or not drive.is_dir():
        return jsonify({"error": "Drive not found"}), 400

    if not EDID_DIR.exists():
        return jsonify({"error": "Local EDID directory not found"}), 500

    exported = []
    skipped = []

    for file in EDID_DIR.glob("*.bin"):
        try:
            edid = file.read_bytes()
        except OSError:
            continue

        target = drive / file.name

        if target.exists():
            try:
                if target.read_bytes() == edid:
                    skipped.append(file.name)
                    continue
            except OSError:
                skipped.append(file.name)
                continue

        target.write_bytes(edid)
        exported.append(file.name)

    return jsonify({
        "exported": exported,
        "skipped": skipped
    })
