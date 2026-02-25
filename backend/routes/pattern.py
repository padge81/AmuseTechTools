import os
import subprocess
import threading

from flask import Blueprint, request, jsonify

from backend.core.edid.drm import list_connectors
from backend.core.pattern.service import pattern_worker

pattern_bp = Blueprint("pattern_api", __name__, url_prefix="/pattern")
_DISPLAY_MANAGER_SERVICE = os.environ.get("PATTERN_DISPLAY_MANAGER_SERVICE", "lightdm")
# Optional fallback for environments that require DRM master handover.
_FORCE_GLOBAL_DRM_CONTROL = os.environ.get("PATTERN_FORCE_GLOBAL_DRM_CONTROL", "0") == "1"

_ownership_lock = threading.Lock()
_owned_connectors = set()
_display_manager_stopped = False


def _global_drm_requested(data):
    if _FORCE_GLOBAL_DRM_CONTROL:
        return True

    value = data.get("global_drm_control", False)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


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


def _ensure_global_drm_control(requested=False):
    global _display_manager_stopped

    if not (_FORCE_GLOBAL_DRM_CONTROL or requested):
        return True, None

    if _display_manager_stopped:
        return True, None

    dm_ok = _set_display_manager(enabled=False)
    if not dm_ok:
        return False, f"failed to stop display manager service '{_DISPLAY_MANAGER_SERVICE}'"

    _display_manager_stopped = True
    return True, None


def _maybe_release_global_drm_control(requested=False):
    global _display_manager_stopped

    if not (_FORCE_GLOBAL_DRM_CONTROL or requested):
        return True, None

    if not _display_manager_stopped or _owned_connectors:
        return True, None

    dm_ok = _set_display_manager(enabled=True)
    if not dm_ok:
        return False, f"failed to start display manager service '{_DISPLAY_MANAGER_SERVICE}'"

    _display_manager_stopped = False
    return True, None


@pattern_bp.route("/outputs", methods=["GET"])
def outputs():
    return jsonify(list_connectors())


@pattern_bp.route("/capabilities", methods=["GET"])
def capabilities():
    return jsonify({
        "renderer": "gstreamer-kmssink",
        "display_control_scope": "per-connector-reservation",
        "supports_connector_selection": True,
        "force_global_drm_control": _FORCE_GLOBAL_DRM_CONTROL,
    })


@pattern_bp.route("/control", methods=["POST"])
def control():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    use_global_drm_control = _global_drm_requested(data)

    if action not in {"take", "release"}:
        return jsonify({"ok": False, "error": "invalid action"}), 400

    connector_id, error_response, code = _parse_connector_id(data)
    if error_response:
        return error_response, code

    with _ownership_lock:
        if action == "take":
            if use_global_drm_control:
                ok, err = _ensure_global_drm_control(requested=True)
                if not ok:
                    return jsonify({"ok": False, "error": err}), 500

            _owned_connectors.add(connector_id)
            return jsonify({
                "ok": True,
                "action": action,
                "connector_id": connector_id,
                "owned_connectors": sorted(_owned_connectors),
                "global_drm_control": use_global_drm_control,
                "message": "Connector reserved for pattern output."
                if not use_global_drm_control
                else "Connector reserved and global DRM control acquired.",
            })

        pattern_worker.stop(connector_id)
        _owned_connectors.discard(connector_id)

        ok, err = (True, None)
        if use_global_drm_control or _FORCE_GLOBAL_DRM_CONTROL:
            ok, err = _maybe_release_global_drm_control(requested=use_global_drm_control)
        if not ok:
            return jsonify({"ok": False, "error": err}), 500

        return jsonify({
            "ok": True,
            "action": action,
            "connector_id": connector_id,
            "owned_connectors": sorted(_owned_connectors),
            "global_drm_control": use_global_drm_control or _FORCE_GLOBAL_DRM_CONTROL,
            "message": "Connector released.",
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

        ok, err = _ensure_global_drm_control(requested=False)
        if not ok:
            return jsonify({"ok": False, "error": err}), 500

    try:
        if mode == "solid":
            pattern_worker.start_solid_color(connector_id, data.get("color", "#ffffff"))
        else:
            pattern_worker.start_colorbars(connector_id)
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

    return jsonify({
        "ok": True,
        "connector_id": connector_id,
        "mode": mode,
        "global_drm_control": _FORCE_GLOBAL_DRM_CONTROL,
    })


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
