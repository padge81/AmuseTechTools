import os
import subprocess
import threading

from flask import Blueprint, request, jsonify

from backend.core.edid.drm import list_connectors
from backend.core.pattern.service import pattern_worker

pattern_bp = Blueprint("pattern_api", __name__, url_prefix="/pattern")
_DISPLAY_MANAGER_SERVICE = os.environ.get("PATTERN_DISPLAY_MANAGER_SERVICE", "lightdm")
_ownership_lock = threading.Lock()
_owned_connectors = set()
_display_manager_stopped = False


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


@pattern_bp.route("/capabilities", methods=["GET"])
def capabilities():
    return jsonify({
        "renderer": "gstreamer-kmssink",
        "display_control_scope": "global-drm-master",
        "supports_connector_selection": True,
    })


@pattern_bp.route("/control", methods=["POST"])
def control():
    global _display_manager_stopped

    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action not in {"take", "release"}:
        return jsonify({"ok": False, "error": "invalid action"}), 400

    connector_id, error_response, code = _parse_connector_id(data)
    if error_response:
        return error_response, code

    with _ownership_lock:
        if action == "take":
            if not _display_manager_stopped:
                dm_ok = _set_display_manager(enabled=False)
                if not dm_ok:
                    return jsonify({
                        "ok": False,
                        "error": f"failed to stop display manager service '{_DISPLAY_MANAGER_SERVICE}'",
                    }), 500
                _display_manager_stopped = True

            _owned_connectors.add(connector_id)
            return jsonify({
                "ok": True,
                "action": action,
                "connector_id": connector_id,
                "owned_connectors": sorted(_owned_connectors),
                "message": "Display control taken for connector (display manager stopped globally for DRM master).",
            })

        pattern_worker.stop(connector_id)
        _owned_connectors.discard(connector_id)

        if _display_manager_stopped and not _owned_connectors:
            dm_ok = _set_display_manager(enabled=True)
            if not dm_ok:
                return jsonify({
                    "ok": False,
                    "error": f"failed to start display manager service '{_DISPLAY_MANAGER_SERVICE}'",
                }), 500
            _display_manager_stopped = False

        return jsonify({
            "ok": True,
            "action": action,
            "connector_id": connector_id,
            "owned_connectors": sorted(_owned_connectors),
            "message": "Display released for connector.",
        })


@pattern_bp.route("/start", methods=["POST"])
def start():
    data = request.get_json(silent=True) or {}

    connector_id, error_response, code = _parse_connector_id(data)
    if error_response:
        return error_response, code

    mode = data.get("mode", "colorbars")

    with _ownership_lock:
        if connector_id not in _owned_connectors:
            return jsonify({
                "ok": False,
                "error": "connector is not taken. Use Take Display Control first.",
            }), 409

    try:
        if mode == "solid":
            pattern_worker.start_solid_color(connector_id, data.get("color", "#ffffff"))
        else:
            pattern_worker.start_colorbars(connector_id)
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    return jsonify({"ok": True, "connector_id": connector_id, "mode": mode})


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
