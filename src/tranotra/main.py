"""Flask application factory and main entry point"""

from pathlib import Path

from flask import Flask, jsonify

from tranotra.config import create_app_config
from tranotra.routes import search_bp
from tranotra.infrastructure.database import init_db


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

    # Health check endpoint
    @app.route("/", methods=["GET"])
    def health_check() -> tuple:
        """Health check endpoint

        Returns:
            tuple: JSON response and HTTP status code
        """
        return jsonify({"status": "healthy", "version": "1.0"}), 200

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
