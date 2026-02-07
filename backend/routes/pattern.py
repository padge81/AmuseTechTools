# backend/routes/pattern.py

from flask import Blueprint, request, jsonify
import subprocess

pattern_bp = Blueprint("pattern", __name__)
state = None  # injected from app startup

@pattern_bp.route("/pattern/control", methods=["POST"])
def control():
    action = request.json.get("action")

    if action == "take":
        subprocess.run(["systemctl", "stop", "lightdm"])
        state.update(active=True)

    elif action == "release":
        state.update(active=False)
        subprocess.run(["systemctl", "start", "lightdm"])

    return jsonify({"ok": True})


@pattern_bp.route("/pattern/solid", methods=["POST"])
def solid():
    data = request.json
    state.update(
        mode="solid",
        value=data.get("color"),
        output=data.get("connector_id"),
    )
    return jsonify({"ok": True})
