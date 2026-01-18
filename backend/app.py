from flask import Flask, render_template
from backend.routes import system, edid
from backend.core.system.version import get_version


def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static"
    )

    # Register blueprints
    app.register_blueprint(system.bp)
    app.register_blueprint(edid.bp)

    # Main menu
    @app.route("/")
    def index():
        return render_template(
            "index.html",
            version=get_version()
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080)

