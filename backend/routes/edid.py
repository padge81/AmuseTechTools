from flask import Blueprint, jsonify, request, render_template

bp = Blueprint("edid", __name__, url_prefix="/edid")

@bp.route("/")
def page():
    return render_template("edid_tools.html")

@bp.route("/read")
def read_edid():
    return jsonify(status="stub")

@bp.route("/write", methods=["POST"])
def write_edid():
    return jsonify(status="stub")
from flask import Blueprint, jsonify, request, render_template
from backend.core.edid.read import read_edid_drm
from backend.core.edid.decode import decode_basic
from backend.core.edid.compare import find_matching_edid
from backend.core.edid.exceptions import EDIDError

bp = Blueprint("edid", __name__, url_prefix="/edid")


@bp.route("")
def edid_page():
    return render_template("edid_tools.html")


@bp.route("/read", methods=["GET"])
def read_edid_route():
    try:
        from backend.core.edid.read import read_edid_drm
        from backend.core.edid.decode import decode_basic
        from backend.core.edid.compare import find_matching_edid

        edid = read_edid_drm("/sys/class/drm/card0-HDMI-A-1/edid")

        matches = find_matching_edid(edid, "edid_files")
        decoded = decode_basic(edid)

        return {
            "ok": True,
            "edid_hex": edid.hex(),
            "decoded": decoded,
            "matches": matches,
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}, 400

