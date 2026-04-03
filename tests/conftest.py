"""Shared pytest configuration and fixtures"""

import os
import sys
from pathlib import Path

import pytest

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set testing environment
os.environ["FLASK_ENV"] = "testing"
os.environ["GEMINI_API_KEY"] = "test-key-dummy-value"


@pytest.fixture
def app():
    """Create Flask app for testing

    Yields:
        Flask: Test application instance
    """
    from tranotra.main import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client

    Args:
        app: Flask application fixture

    Returns:
        FlaskClient: Test client for making requests
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner

    Args:
        app: Flask application fixture

    Returns:
        FlaskCliRunner: CLI test runner
    """
    return app.test_cli_runner()
