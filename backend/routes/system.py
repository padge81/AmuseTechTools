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
    subprocess.Popen(["git", "-C", "/home/att/AmuseTechTools", "pull"])
    return jsonify({"status": "ok"})
