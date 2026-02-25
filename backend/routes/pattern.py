from flask import Blueprint, request, jsonify

from backend.core.edid.drm import list_connectors
from backend.core.pattern.service import pattern_worker

pattern_bp = Blueprint("pattern", __name__, url_prefix="/pattern")


@pattern_bp.route("/outputs", methods=["GET"])
def outputs():
    return jsonify(list_connectors())


@pattern_bp.route("/control", methods=["POST"])
def control():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    connector_id = data.get("connector_id")

    if action not in {"take", "release"}:
        return jsonify({"ok": False, "error": "invalid action"}), 400

    if connector_id is None:
        return jsonify({"ok": False, "error": "connector_id is required"}), 400

    try:
        connector_id = int(connector_id)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "connector_id must be an integer"}), 400

    if action == "take":
        pattern_worker.start_kmscube(connector_id)
    else:
        pattern_worker.stop(connector_id)

    return jsonify({"ok": True, "connector_id": connector_id, "action": action})


@pattern_bp.route("/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}

    try:
        connector_id = int(data.get("connector_id", 33))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "connector_id must be an integer"}), 400

    mode = data.get("mode")
    color = data.get("color")

    pattern_worker.start_kmscube(connector_id)

    response = {"ok": True, "connector_id": connector_id}
    if mode == "solid" and color:
        response["note"] = "kmscube started for selected connector (solid colour rendering depends on kmscube build/options)"
    return jsonify(response)


@pattern_bp.route("/stop", methods=["POST"])
def stop():
    data = request.get_json(silent=True) or {}
    connector_id = data.get("connector_id")

    if connector_id is None:
        pattern_worker.stop()
        return jsonify({"ok": True, "scope": "all"})

    try:
        connector_id = int(connector_id)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "connector_id must be an integer"}), 400

    pattern_worker.stop(connector_id)
    return jsonify({"ok": True, "connector_id": connector_id})
