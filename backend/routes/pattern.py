from flask import Blueprint, request, jsonify
from app import Pattern_Worker
import subprocess

bp = Blueprint("pattern", __name__, url_prefix="/pattern")


@pattern_bp.route("/pattern/control", methods=["POST"])
def control():
    action = request.json.get("action")
    state = pattern_bp.state  # <-- THIS is the fix

    if action == "take":
        subprocess.run(["systemctl", "stop", "lightdm"], check=False)
        state.update(active=True)

    elif action == "release":
        state.update(active=False)
        subprocess.run(["systemctl", "start", "lightdm"], check=False)

    return jsonify({"ok": True})


@pattern_bp.route("/pattern/solid", methods=["POST"])
def solid():
    state = pattern_bp.state  # <-- and here

    data = request.json
    state.update(
        mode="solid",
        value=data.get("color"),
        output=data.get("connector_id"),
    )

    return jsonify({"ok": True})
