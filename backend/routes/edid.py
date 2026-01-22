from flask import Blueprint, jsonify, request
from pathlib import Path
import os

from backend.core.edid.read import read_edid_drm
from backend.core.edid.compare import find_matching_edid

bp = Blueprint("edid", __name__, url_prefix="/edid")

# Directory where saved EDID .bin files live
EDID_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]   # backend/routes → backend → repo root
    / "edid_files"
)



# --------------------------------------------------
# READ EDID FROM DRM CONNECTOR
# --------------------------------------------------
@bp.route("/read")
def read_edid():
    connector = request.args.get("connector")

    if not connector:
        return jsonify({"error": "No connector specified"}), 400

    path = f"/sys/class/drm/{connector}/edid"

    if not os.path.exists(path):
        return jsonify({"error": f"EDID not found for {connector}"}), 400

    try:
        edid = read_edid_drm(path)
        return jsonify({
            "connector": connector,
            "edid_hex": edid.hex()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# --------------------------------------------------
# MATCH EDID AGAINST SAVED FILES
# --------------------------------------------------
@bp.route("/match", methods=["POST"])
def match_edid():
    data = request.get_json()
    connector = data.get("connector")

    if not connector:
        return jsonify({"error": "No connector specified"}), 400

    path = f"/sys/class/drm/{connector}/edid"
    print("MATCH DIR:", EDID_DIR)
    try:
        edid = read_edid_drm(path)
        matches = find_matching_edid(edid, EDID_DIR)

        return jsonify({
            "matches": matches
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# --------------------------------------------------
# LIST AVAILABLE DRM CONNECTORS
# --------------------------------------------------
@bp.route("/connectors")
def list_connectors():
    drm_path = "/sys/class/drm"
    connectors = []

    for entry in os.listdir(drm_path):
        edid_path = os.path.join(drm_path, entry, "edid")
        if not os.path.exists(edid_path):
            continue

        try:
            # Validate EDID header only
            read_edid_drm(edid_path)
            connectors.append(entry)
        except Exception:
            pass

    return jsonify(connectors)
