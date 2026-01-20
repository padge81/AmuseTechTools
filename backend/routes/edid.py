from flask import Blueprint, jsonify, request
from backend.core.edid.read import read_edid_drm
import os

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
