import os
import subprocess

from flask import Blueprint, request, jsonify

from backend.core.edid.drm import list_connectors
from backend.core.pattern.service import pattern_worker

pattern_bp = Blueprint("pattern", __name__, url_prefix="/pattern")
_DISPLAY_MANAGER_SERVICE = os.environ.get("PATTERN_DISPLAY_MANAGER_SERVICE", "lightdm")


def _parse_connector_id(data, default=None):
    value = data.get("connector_id", default)
    if value is None:
        return None, jsonify({"ok": False, "error": "connector_id is required"}), 400

    try:
        return int(value), None, None
    except (TypeError, ValueError):
        return None, jsonify({"ok": False, "error": "connector_id must be an integer"}), 400


def _set_display_manager(enabled):
    action = "start" if enabled else "stop"
    result = subprocess.run(["systemctl", action, _DISPLAY_MANAGER_SERVICE], check=False)
    return result.returncode == 0


@pattern_bp.route("/outputs", methods=["GET"])
def outputs():
    return jsonify(list_connectors())


def _parse_connector_id(data, default=None):
    value = data.get("connector_id", default)
    if value is None:
        return None, jsonify({"ok": False, "error": "connector_id is required"}), 400

    try:
        return int(value), None, None
    except (TypeError, ValueError):
        return None, jsonify({"ok": False, "error": "connector_id must be an integer"}), 400


@pattern_bp.route("/outputs", methods=["GET"])
def outputs():
    return jsonify(list_connectors())


@pattern_bp.route("/control", methods=["POST"])
def control():
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action not in {"take", "release"}:
        return jsonify({"ok": False, "error": "invalid action"}), 400

    if action == "take":
        dm_ok = _set_display_manager(enabled=False)
        if not dm_ok:
            return jsonify({
                "ok": False,
                "error": f"failed to stop display manager service '{_DISPLAY_MANAGER_SERVICE}'",
            }), 500

        return jsonify({
            "ok": True,
            "action": action,
            "display_manager": _DISPLAY_MANAGER_SERVICE,
            "message": "Display manager stopped. You can now start a KMS pattern.",
        })

    # release
    pattern_worker.stop()
    dm_ok = _set_display_manager(enabled=True)
    if not dm_ok:
        return jsonify({
            "ok": False,
            "error": f"failed to start display manager service '{_DISPLAY_MANAGER_SERVICE}'",
        }), 500

    return jsonify({
        "ok": True,
        "action": action,
        "display_manager": _DISPLAY_MANAGER_SERVICE,
        "message": "Display manager started and pattern processes stopped.",
    })


@pattern_bp.route("/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}

    connector_id, error_response, code = _parse_connector_id(data, default=33)
    if error_response:
        return error_response, code

    mode = data.get("mode")
    color = data.get("color")

    try:
        start_meta = pattern_worker.start_kmscube(connector_id)
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    response = {"ok": True, "connector_id": connector_id}
    if not start_meta["connector_selection_supported"]:
        response["warning"] = "This kmscube build does not support connector selection; pattern may appear on the default connector."
    if mode == "solid" and color:
        response["note"] = "Requested solid colour via kmscube start (actual rendering depends on kmscube build/options)."
    return jsonify(response)


@pattern_bp.route("/stop", methods=["POST"])
def stop():
    data = request.get_json(silent=True) or {}
    connector_id = data.get("connector_id")

    if connector_id is None:
        pattern_worker.stop()
        return jsonify({"ok": True, "scope": "all"})

    connector_id, error_response, code = _parse_connector_id(data)
    if error_response:
        return error_response, code

    pattern_worker.stop(connector_id)
    return jsonify({"ok": True, "connector_id": connector_id})
