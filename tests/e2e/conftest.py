"""End-to-End test pytest configuration and fixtures"""

import os
import sys
from pathlib import Path

import pytest

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Set testing environment
os.environ["FLASK_ENV"] = "testing"
os.environ["GEMINI_API_KEY"] = "test-key-dummy-value"


@pytest.fixture
def app():
    """Create Flask app for E2E testing

    Yields:
        Flask: Test application instance
    """
    from tranotra.main import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client for E2E testing

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client for making requests
    """
    # Fix werkzeug version issue
    import werkzeug
    if not hasattr(werkzeug, '__version__'):
        werkzeug.__version__ = '3.0.0'

    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner for E2E testing

    Args:
        app: Flask application fixture

    Returns:
        FlaskCliRunner: CLI test runner
    """
    return app.test_cli_runner()


@pytest.fixture
def clear_cache():
    """Clear search results cache"""
    from tranotra.routes import results_cache
    results_cache.clear()
    yield
    results_cache.clear()


@pytest.fixture(autouse=True)
def cleanup_cache_after_test():
    """Auto-cleanup cache after each test to prevent state leakage between tests"""
    from tranotra.routes import results_cache
    yield
    # Cleanup after test
    results_cache.clear()
