from flask import Flask, render_template
from backend.system import system_action, get_version

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static",
)

@app.route("/")
def index():
    return render_template("index.html", version=get_version())


@app.route("/edid")
def edid_tools():
    return render_template("edid_tools.html")


@app.route("/pattern-generator")
def pattern_generator():
    return render_template("pattern_generator.html")


@app.route("/camera")
def camera():
    return render_template("camera.html")


@app.route("/input-output")
def input_output():
    return render_template("input_output.html")


# ---- SYSTEM ACTIONS ----

@app.route("/exit")
def exit_browser():
    system_action("exit")
    return "Exiting..."


@app.route("/reboot")
def reboot():
    system_action("reboot")
    return "Rebooting..."


@app.route("/shutdown")
def shutdown():
    system_action("shutdown")
    return "Shutting down..."


@app.route("/update")
def update():
    system_action("update")
    return "Updating..."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
