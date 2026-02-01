from flask import Blueprint, request, jsonify

from backend.core.pattern.state import set_state, get_state
from backend.core.edid.drm import list_connectors

bp = Blueprint("pattern", __name__, url_prefix="/api/pattern")

# ---------------------------------------
# List Outputs (DRM connectors)
# ---------------------------------------
@bp.route("/outputs")
def outputs():
    return jsonify(list_connectors())

# ---------------------------------------
# Set Solid Colour
# ---------------------------------------
@bp.route("/solid", methods=["POST"])
def solid_color():
    data = request.json or {}

    output = data.get("output")
    color = data.get("color")

    if not output or not color:
        return jsonify({"error": "Missing output or color"}), 400

    set_state(
        output=output,
        mode="solid",
        value=color,
        active=True
    )

    return jsonify({"ok": True})

# ---------------------------------------
# Stop Pattern Generator
# ---------------------------------------
@bp.route("/stop", methods=["POST"])
def stop():
    set_state(active=False)
    return jsonify({"ok": True})

# ---------------------------------------
# Status
# ---------------------------------------
@bp.route("/status")
def status():
    return jsonify(get_state())
