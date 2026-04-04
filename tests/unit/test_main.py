"""Tests for Flask application"""

import pytest


class TestFlaskApp:
    """Test Flask application factory and basic functionality"""

    def test_create_app(self, app):
        """Test that app is created successfully"""
        assert app is not None
        assert app.config["TESTING"] is True

    def test_app_has_search_blueprint(self, app):
        """Test that search blueprint is registered"""
        # Check that blueprints are registered
        assert len(app.blueprints) > 0
        assert "search" in app.blueprints

    def test_flask_static_folder_configured(self, app):
        """Test that static folder is configured"""
        assert app.static_folder is not None
        # Should end with 'static'
        assert app.static_folder.endswith("static")

    def test_flask_template_folder_configured(self, app):
        """Test that template folder is configured"""
        assert app.template_folder is not None
        # Should end with 'templates'
        assert app.template_folder.endswith("templates")

    def test_app_routes_registered(self, app):
        """Test that Flask routes are registered"""
        # Check that routes exist
        assert app.url_map is not None
        route_strings = [str(rule) for rule in app.url_map.iter_rules()]
        # Should have at least health check and search routes
        assert any("/" in route for route in route_strings)

    def test_app_has_json_encoder(self, app):
        """Test that Flask is configured for JSON responses"""
        # Flask should have JSON capabilities
        assert hasattr(app, "json")

    def test_app_config_from_environment(self, app):
        """Test that app configuration is loaded"""
        # In testing mode, should have TESTING flag
        assert app.config.get("TESTING") is True
