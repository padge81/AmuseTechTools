from flask import Blueprint, request, jsonify
import subprocess
import os

from backend.core.pattern.state import set_state, get_state
from backend.core.edid.drm import list_connectors

bp = Blueprint("pattern", __name__, url_prefix="/api/pattern")

# -------------------------------------------------
# Display ownership handling
# -------------------------------------------------

DISPLAY_LOCK = "/run/amuse_display_owner"


def get_owner():
    try:
        with open(DISPLAY_LOCK, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "desktop"


def set_owner(owner: str):
    os.makedirs(os.path.dirname(DISPLAY_LOCK), exist_ok=True)
    with open(DISPLAY_LOCK, "w") as f:
        f.write(owner)


# -------------------------------------------------
# Take / Release display
# -------------------------------------------------

@bp.route("/display/take", methods=["POST"])
def take_display():
    if get_owner() == "tool":
        return jsonify({"status": "already-owned"})

    # Stop desktop if present (safe on headless)
    subprocess.run(
        ["systemctl", "stop", "lightdm"],
        check=False,
        timeout=5
    )

    set_owner("tool")
    return jsonify({"status": "ok"})


@bp.route("/display/release", methods=["POST"])
def release_display():
    # Kill any running test pattern tools
    subprocess.run(["pkill", "-f", "modetest"], check=False)
    subprocess.run(["pkill", "-f", "kmscube"], check=False)

    # Restart desktop if available
    subprocess.run(
        ["systemctl", "start", "lightdm"],
        check=False,
        timeout=5
    )

    set_owner("desktop")
    return jsonify({"status": "ok"})


# -------------------------------------------------
# Outputs (DRM connectors)
# -------------------------------------------------

@bp.route("/outputs", methods=["GET"])
def outputs():
    return jsonify(list_connectors())


# -------------------------------------------------
# Solid colour pattern
# -------------------------------------------------

@bp.route("/solid", methods=["POST"])
def solid_color():
    if get_owner() != "tool":
        return jsonify({"error": "display not owned"}), 409

    data = request.json or {}
    output = data.get("output")
    color = data.get("color")

    if not output or not color:
        return jsonify({"error": "missing output or color"}), 400

    set_state(
        output=output,
        mode="solid",
        value=color,
        active=True
    )

    return jsonify({"ok": True})


# -------------------------------------------------
# Stop pattern generator
# -------------------------------------------------

@bp.route("/stop", methods=["POST"])
def stop():
    set_state(active=False)
    return jsonify({"ok": True})


# -------------------------------------------------
# Status
# -------------------------------------------------

@bp.route("/status", methods=["GET"])
def status():
    return jsonify({
        "owner": get_owner(),
        "state": get_state()
    })
