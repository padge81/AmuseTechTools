from flask import Blueprint, request, jsonify
import subprocess

from backend.core.pattern.service import pattern_worker

pattern_bp = Blueprint("pattern", __name__, url_prefix="/pattern")


@pattern_bp.route("/control", methods=["POST"])
def control():
    action = request.json.get("action")

    if action == "take":
        subprocess.run(["systemctl", "stop", "lightdm"], check=False)

    elif action == "release":
        pattern_worker.stop()
        subprocess.run(["systemctl", "start", "lightdm"], check=False)

    return jsonify({"ok": True})


@pattern_bp.route("/start", methods=["POST"])
def start():
    data = request.json or {}
    connector_id = data.get("connector_id", 33)

    pattern_worker.start_kmscube(connector_id)

    return jsonify({"ok": True})


@pattern_bp.route("/stop", methods=["POST"])
def stop():
    pattern_worker.stop()
    return jsonify({"ok": True})
