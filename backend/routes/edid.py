from flask import Blueprint, jsonify, request
from pathlib import Path
import os

from backend.core.edid.read import read_edid_drm
from backend.core.edid.compare import find_matching_edid
from backend.core.edid.decode import decode_basic, edid_to_hex

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
    if not data or "edid_hex" not in data:
        return jsonify({"error": "No EDID provided"}), 400

    try:
        edid = bytes.fromhex(data["edid_hex"])
    except ValueError:
        return jsonify({"error": "Invalid EDID hex"}), 400

    matches = find_matching_edid(edid, EDID_DIR)

    return jsonify({
        "matches": matches
    })

@bp.route("/save", methods=["POST"])
def save_edid():
    data = request.get_json()

    edid_hex = data.get("edid_hex")
    filename = data.get("filename")

    if not edid_hex or not filename:
        return jsonify({"error": "Missing EDID or filename"}), 400

    if not filename.lower().endswith(".bin"):
        return jsonify({"error": "Filename must end with .bin"}), 400

    target = EDID_DIR / filename

    if target.exists():
        return jsonify({"error": "File already exists"}), 400

    try:
        edid = bytes.fromhex(edid_hex)
        target.write_bytes(edid)
        return jsonify({"saved": True, "filename": filename})
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



# ----------------------------------------------------
# Decode End Point
# ----------------------------------------------------
@bp.route("/decode", methods=["POST"])
def decode_edid():
    data = request.get_json()

    edid_hex = data.get("edid_hex")
    if not edid_hex:
        return jsonify({"error": "No EDID provided"}), 400

    try:
        edid = bytes.fromhex(edid_hex)

        basic = decode_basic(edid)

        decoded_text = (
            "Decoded EDID\n"
            "============================\n\n"
            f"Manufacturer      : {basic['manufacturer']}\n"
            f"Product Code      : {basic['product_code']}\n"
            f"Serial Number     : {basic['serial']}\n"
            f"Manufactured Date : Week {basic['week']} / {basic['year']}\n"
            f"Extensions        : {basic['extensions']}\n\n"
            "Raw EDID Hex Dump\n"
            "----------------------------\n"
            f"{edid_to_hex(edid)}"
        )

        return jsonify({
            "decoded": decoded_text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400