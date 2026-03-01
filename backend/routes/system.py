from flask import Blueprint, jsonify
import subprocess

bp = Blueprint("system", __name__, url_prefix="/system")


    
@bp.route("/exit_browser", methods=["POST"])
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
    Safe update:
      - pull latest code
      - preserve runtime files
      - restart service
    """
    import subprocess

    cmd = """
    set -e
    cd ~/AmuseTechTools
    git pull origin main
    nohup bash -lc "sleep 1; systemctl --user restart amuse-tech-tools.service" >/dev/null 2>&1 &
    """

    subprocess.Popen(["bash", "-lc", cmd])
    return jsonify({"status": "ok", "mode": "pull"})
