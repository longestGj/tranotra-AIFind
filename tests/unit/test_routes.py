"""Tests for Flask routes/blueprints"""

import pytest


class TestSearchBlueprint:
    """Test search blueprint"""

    def test_search_blueprint_exists(self, app):
        """Test that search blueprint is registered"""
        assert "search" in app.blueprints

    def test_search_blueprint_has_routes(self, app):
        """Test that search blueprint has routes"""
        # Get all routes for the search blueprint
        search_routes = [
            rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith("search.")
        ]
        assert len(search_routes) > 0
