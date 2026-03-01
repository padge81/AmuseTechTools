from flask import Blueprint, jsonify
import subprocess

bp = Blueprint("system", __name__, url_prefix="/system")

@bp.route("/osk/show", methods=["POST"])
def osk_show():
    # Start if not running
    subprocess.Popen(["pgrep", "-x", "onboard"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Try to show/unhide the Onboard window; if it's not there yet, just launch onboard
    subprocess.Popen(["bash", "-lc", 'wmctrl -xa "onboard.Onboard" -b remove,hidden 2>/dev/null || onboard >/dev/null 2>&1 &'])
    return jsonify({"status": "ok"})

@bp.route("/osk/hide", methods=["POST"])
def osk_hide():
    subprocess.Popen(["bash", "-lc", 'wmctrl -xa "onboard.Onboard" -b add,hidden 2>/dev/null || true'])
    return jsonify({"status": "ok"})

@bp.route("/osk/toggle", methods=["POST"])
def osk_toggle():
    # Toggle hidden state
    subprocess.Popen(["bash", "-lc", r'''
      if wmctrl -lx | grep -qi "onboard\.Onboard"; then
        if xprop -id "$(wmctrl -lx | awk '/onboard\.Onboard/{print $1; exit}')" _NET_WM_STATE 2>/dev/null | grep -q "_NET_WM_STATE_HIDDEN"; then
          wmctrl -xa "onboard.Onboard" -b remove,hidden
        else
          wmctrl -xa "onboard.Onboard" -b add,hidden
        fi
      else
        onboard >/dev/null 2>&1 &
      fi
    '''])
    return jsonify({"status": "ok"})
    
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
