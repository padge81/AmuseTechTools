from flask import Blueprint, request, jsonify
from pattern.state import set_state, get_state
from backend.core.edid.drm import list_connectors

bp = Blueprint("pattern", __name__, url_prefix="/api/pattern")

#---------------------------------------
# List Outputs
#---------------------------------------
@bp.route("/outputs")
def outputs():
    return jsonify(list_connectors())
    
#---------------------------------------
# Set Solid Colour
#---------------------------------------   
@bp.route("/solid", methods=["POST"])
def solid_color():
    data = request.json
    output = data["output"]
    color = data["color"]

    set_state(
        output=output,
        mode="solid",
        value=color,
        active=True
    )

    return jsonify({"ok": True})

#---------------------------------------
# Set Test Pattern
#--------------------------------------- 
@bp.route("/pattern", methods=["POST"])
def test_pattern():
    data = request.json

    set_state(
        output=data["output"],
        mode="pattern",
        value=data["pattern"],
        active=True
    )

    return jsonify({"ok": True})
    
#---------------------------------------
# Stop Start Screen Saver
#--------------------------------------- 
@bp.route("/saver/start", methods=["POST"])
def start_saver():
    data = request.json

    set_state(
        output=data["output"],
        mode="saver",
        value=None,
        active=True
    )
    return jsonify({"ok": True})

@bp.route("/stop", methods=["POST"])
def stop():
    set_state(active=False)
    return jsonify({"ok": True})

#---------------------------------------
# Status Endpoint
#--------------------------------------- 
@bp.route("/status")
def status():
    return jsonify(get_state())