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
