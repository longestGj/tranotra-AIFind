"""Flask application factory and main entry point"""

from pathlib import Path

from flask import Flask, jsonify, render_template

from tranotra.config import create_app_config
from tranotra.routes import search_bp
from tranotra.routes_analytics import analytics_bp
from tranotra.infrastructure.database import init_db
from tranotra.db import get_today_statistics


def create_app() -> Flask:
    """Flask app factory

    Returns:
        Flask: Configured Flask application instance
    """
    # Use absolute paths based on this file's location
    base_dir = Path(__file__).parent.parent.parent

    app = Flask(
        __name__,
        static_folder=str(base_dir / "static"),
        template_folder=str(base_dir / "templates")
    )

    # Load configuration
    create_app_config(app)

    # Initialize database
    try:
        database_url = app.config.get("DATABASE_URL", "sqlite:///./data/leads.db")
        init_db(database_url)
    except Exception as e:
        app.logger.error(f"Failed to initialize database: {e}")

    # Register blueprints
    app.register_blueprint(search_bp)
    app.register_blueprint(analytics_bp)

    # Home page endpoint (Search form)
    @app.route("/", methods=["GET"])
    def home() -> tuple:
        """Home page with search form

        Returns:
            tuple: HTML response and HTTP status code
        """
        try:
            stats = get_today_statistics()
        except Exception as e:
            app.logger.error(f"Error fetching statistics: {e}")
            stats = {"searches": 0, "new_companies": 0, "dedup_rate": 0}

        return render_template("index.html", stats=stats), 200

    # Dashboard endpoint
    @app.route("/dashboard", methods=["GET"])
    def dashboard() -> tuple:
        """Analytics dashboard page

        Returns:
            tuple: HTML response and HTTP status code
        """
        return render_template("dashboard.html"), 200

    return app


if __name__ == "__main__":
    import os
    from tranotra.config import load_config

    app = create_app()
    config = load_config()

    # Use configuration values for host, port, and debug mode
    app.run(
        host=config["FLASK_HOST"],
        port=config["FLASK_PORT"],
        debug=config["FLASK_DEBUG"]
    )
