from flask import Blueprint, jsonify, request
from pathlib import Path
import os
import shutil
import hashlib

bp = Blueprint("usb", __name__, url_prefix="/usb")

EDID_DIR = Path("edid_files")
USB_MOUNT_BASES = ["/media", "/mnt"]


# ----------------------------
# Helpers
# ----------------------------

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def list_usb_mounts():
    mounts = []

    for base in USB_MOUNT_BASES:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for user_dir in base_path.iterdir():
            if not user_dir.is_dir():
                continue

            # If this dir itself is a mount, include it
            mounts.append(str(user_dir))

            # Also scan one level deeper (common auto-mount layout)
            for p in user_dir.iterdir():
                if p.is_dir():
                    mounts.append(str(p))

    # Remove duplicates + non-mounted paths
    return sorted(set(mounts))


# ----------------------------
# USB STATUS
# ----------------------------

@bp.route("/status")
def usb_status():
    mounts = list_usb_mounts()
    result = []

    for m in mounts:
        result.append({
            "path": m,
            "name": os.path.basename(m),
        })

    return jsonify(result)


# ----------------------------
# SCAN USB FOR EDIDS
# ----------------------------

@bp.route("/scan")
def usb_scan():
    mount = request.args.get("mount")
    if not mount or not os.path.isdir(mount):
        return jsonify({"error": "Invalid mount"}), 400

    mount_path = Path(mount)

    usb_bins = list(mount_path.glob("*.bin"))
    local_hashes = {
        file_hash(f): f.name
        for f in EDID_DIR.glob("*.bin")
    }

    files = []
    for f in usb_bins:
        h = file_hash(f)
        files.append({
            "name": f.name,
            "exists": h in local_hashes,
        })

    return jsonify(files)


# ----------------------------
# IMPORT
# ----------------------------

@bp.route("/import", methods=["POST"])
def usb_import():
    data = request.json
    mount = data.get("mount")
    files = data.get("files", [])

    if not mount or not os.path.isdir(mount):
        return jsonify({"error": "Invalid mount"}), 400

    imported = []
    skipped = []

    for name in files:
        src = Path(mount) / name
        dst = EDID_DIR / name

        if not src.exists():
            continue

        if dst.exists():
            if file_hash(src) == file_hash(dst):
                skipped.append(name)
                continue

        shutil.copy2(src, dst)
        imported.append(name)

    return jsonify({
        "imported": imported,
        "skipped": skipped
    })


# ----------------------------
# EXPORT
# ----------------------------

@bp.route("/export", methods=["POST"])
def usb_export():
    data = request.json
    mount = data.get("mount")
    files = data.get("files", [])

    if not mount or not os.path.isdir(mount):
        return jsonify({"error": "Invalid mount"}), 400

    exported = []
    skipped = []

    for name in files:
        src = EDID_DIR / name
        dst = Path(mount) / name

        if not src.exists():
            continue

        if dst.exists():
            if file_hash(src) == file_hash(dst):
                skipped.append(name)
                continue

        shutil.copy2(src, dst)
        exported.append(name)

    return jsonify({
        "exported": exported,
        "skipped": skipped
    })
