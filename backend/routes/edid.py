from flask import Blueprint, jsonify, request
from backend.core.edid.read import read_edid_drm
from backend.core.edid.compare import find_matching_edid
from pathlib import Path
import os

EDID_DIR = Path("edid_files")

bp = Blueprint("edid", __name__, url_prefix="/edid")


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
        
@bp.route("/match", methods=["POST"])
def match_edid():
    try:
        data = request.get_json()
        #print("MATCH PAYLOAD:", data)

        edid_hex = data.get("edid_hex")
        if not edid_hex:
            return jsonify({"error": "No EDID provided"}), 400

        edid = bytes.fromhex(edid_hex)
        
    # 🔍 DEBUG LOGGING
    print("EDID FROM UI")
    print("Length:", len(edid))
    print("First 16 bytes:", edid[:16].hex())
    
        matches = find_matching_edid(edid, EDID_DIR)

        return jsonify({
            "matches": matches
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        

@bp.route("/connectors")
def list_connectors():
    drm_path = "/sys/class/drm"
    connectors = []

    for entry in os.listdir(drm_path):
        edid_path = os.path.join(drm_path, entry, "edid")
        if os.path.exists(edid_path):
            try:
                # Try reading header only
                read_edid_drm(edid_path)
                connectors.append(entry)
            except Exception:
                pass

    return jsonify(connectors)