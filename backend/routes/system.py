from flask import Blueprint, jsonify
import subprocess

bp = Blueprint("system", __name__, url_prefix="/system")

@bp.route("/reboot", methods=["POST"])
def reboot():
    subprocess.Popen(["sudo", "/sbin/reboot"])
    return jsonify({"message": "Rebooting"}), 200

@bp.route("/shutdown", methods=["POST"])
def shutdown():
    subprocess.Popen(["sudo", "/sbin/shutdown", "-h", "now"])
    return jsonify({"message": "Shutting down"}), 200

@bp.route("/exit_browser", methods=["POST"])
def exit_browser():
    subprocess.Popen(["sudo", "/usr/bin/pkill", "chromium"])
    return jsonify({"message": "Browser closed"}), 200

@bp.route("/update", methods=["POST"])
def update():
    subprocess.Popen(["sudo", "/usr/bin/git", "-C", "/home/att/AmuseTechTools", "pull"])
    return jsonify({"message": "Updating from GitHub"}), 200
