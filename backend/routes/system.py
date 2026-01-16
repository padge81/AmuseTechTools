from flask import Blueprint, jsonify
import subprocess

bp = Blueprint("system", __name__)

@bp.route("/")
def index():
    from flask import render_template
    return render_template("index.html")

@bp.route("/reboot", methods=["POST"])
def reboot():
    subprocess.Popen(["sudo", "reboot"])
    return jsonify(ok=True)

@bp.route("/shutdown", methods=["POST"])
def shutdown():
    subprocess.Popen(["sudo", "shutdown", "-h", "now"])
    return jsonify(ok=True)

@bp.route("/version")
def version():
    try:
        v = subprocess.check_output(
            ["git", "describe", "--tags", "--dirty", "--always"]
        ).decode().strip()
    except Exception:
        v = "unknown"
    return jsonify(version=v)
