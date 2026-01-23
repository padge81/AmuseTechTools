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
