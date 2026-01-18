from flask import Blueprint, jsonify, request
from backend.core.system.system import system_action

bp = Blueprint("system", __name__, url_prefix="/system")


@bp.route("/action", methods=["POST"])
def do_system_action():
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if not action:
        return jsonify({"error": "No action specified"}), 400

    try:
        system_action(action)
        return jsonify({"status": "ok", "action": action})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
