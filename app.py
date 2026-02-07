from flask import Flask, render_template
from threading import Thread
import os

from backend.routes import system, edid, usb
from backend.core.system.version import get_version
from backend.core.pattern.worker import pattern_worker

def create_app():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )

    # Register blueprints
    app.register_blueprint(system.bp)
    app.register_blueprint(edid.bp)
    app.register_blueprint(usb.bp)
    #app.register_blueprint(pattern.bp)
  

    # Main menu
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

    return app

if __name__ == "__main__":
    app = create_app()
    
        # 🔐 Start worker ONCE (avoid Flask reloader duplication)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        Thread(target=pattern_worker, daemon=True).start()
 
    app.run(host="0.0.0.0", port=8080, debug=True)
