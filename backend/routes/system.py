from flask import Blueprint, jsonify
import subprocess

bp = Blueprint("system", __name__, url_prefix="/system")

@bp.route("/exit", methods=["POST"])
def exit_browser():
    subprocess.Popen(["pkill", "-f", "chromium"])
    return jsonify({"status": "ok"})

@bp.route("/reboot", methods=["POST"])
def reboot():
    subprocess.Popen(["sudo", "/sbin/reboot"])
    return jsonify({"status": "ok"})

@bp.route("/shutdown", methods=["POST"])
def shutdown():
    subprocess.Popen(["sudo", "/sbin/shutdown", "now"])
    return jsonify({"status": "ok"})

@bp.route("/update", methods=["POST"])
def update():
    """
    Appliance mode (/system/update):
      - discard any local changes
      - match remote origin/main exactly
      - restart service after returning HTTP 200
    """
    import subprocess

    cmd = """
    set -euo pipefail
    cd ~/AmuseTechTools
    git fetch --prune origin
    git reset --hard origin/main
    git clean -fd
    # restart the kiosk service after a short delay so the HTTP response is sent
    nohup bash -lc "sleep 1; systemctl --user restart amuse-tech-tools.service" >/dev/null 2>&1 &
    """
    subprocess.Popen(["bash", "-lc", cmd])
    return jsonify({"status": "ok", "mode": "appliance"})
