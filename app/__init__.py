from flask import Flask, render_template

from app.extensions import db


def create_app(test_config=None):
    """Application factory: builds and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev-change-me",
        SQLALCHEMY_DATABASE_URI="sqlite:///mpms.db",
    )
    if test_config:
        app.config.update(test_config)

    from app import db_tuning  # noqa: F401  (SQLite busy timeout + WAL, BL-29)
    db.init_app(app)

    from app.security import init_security
    init_security(app)

    from app import models, models_session  # noqa: F401  (registers tables)
    from app.routes import register_blueprints
    register_blueprints(app)

    from app.session_security import init_session_security
    init_session_security(app)  # BL-09, BL-39: session token + idle timeout

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
