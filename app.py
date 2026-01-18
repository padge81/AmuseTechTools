from flask import Flask, render_template, jsonify
from backend.system import system_action, get_version

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", version=get_version())

@app.route("/edid")
def edid_tools():
    return render_template("edid_tools.html")

@app.route("/pattern")
def pattern():
    return render_template("pattern_generator.html")

@app.route("/camera")
def camera():
    return render_template("camera.html")

@app.route("/io")
def input_output():
    return render_template("input_output.html")

@app.route("/io/<module>")
def io_module(module):
    return render_template(f"{module}.html")

@app.route("/system/<action>", methods=["POST"])
def system(action):
    return jsonify(system_action(action))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
