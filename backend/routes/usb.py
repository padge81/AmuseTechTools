USB_MOUNT_BASES = [
    "/media",
    "/mnt"
]

from flask import Blueprint, jsonify, request
from pathlib import Path

bp = Blueprint("usb", __name__, url_prefix="/usb")


#--------------------------------------
# LIST USB DRIVES
#--------------------------------------

USB_MOUNT_BASES = ["/media", "/mnt"]

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


#--------------------------------------
# IMPORT EDIDS FROM USB
#--------------------------------------

from flask import Blueprint, jsonify
from pathlib import Path

bp = Blueprint("usb", __name__, url_prefix="/usb")

USB_MOUNT_BASES = ["/media", "/mnt"]

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

#--------------------------------------
# EXPORT EDIDS TO USB
#--------------------------------------

@bp.route("/export", methods=["POST"])
def export_edids():
    data = request.get_json()
    drive = Path(data.get("drive", ""))

    if not drive.exists():
        return jsonify({"error": "Drive not found"}), 400

    exported = []
    skipped = []

    for file in EDID_DIR.glob("*.bin"):
        edid = file.read_bytes()

        target = drive / file.name

        if target.exists():
            try:
                if target.read_bytes() == edid:
                    skipped.append(file.name)
                    continue
            except OSError:
                continue

        target.write_bytes(edid)
        exported.append(file.name)

    return jsonify({
        "exported": exported,
        "skipped": skipped
    })
