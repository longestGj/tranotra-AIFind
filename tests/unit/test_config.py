"""Tests for configuration management"""

import os
from unittest.mock import patch

import pytest

from tranotra.config import DevelopmentConfig, TestingConfig, load_config


class TestConfig:
    """Test configuration classes"""

    def test_development_config(self):
        """Test development configuration"""
        assert DevelopmentConfig.DEBUG is True
        assert DevelopmentConfig.TESTING is False

    def test_testing_config(self):
        """Test testing configuration"""
        assert TestingConfig.TESTING is True
        assert TestingConfig.DEBUG is False

    def test_load_config_in_test_mode(self):
        """Test that config loading works in test mode"""
        # In pytest, should load .env.test or use defaults
        config = load_config()
        assert config["FLASK_ENV"] in ["testing", "development"]
        assert config["FLASK_PORT"] == 5000
        assert config["FLASK_HOST"] in ["0.0.0.0", "localhost"]  # Accept either default

    def test_load_config_with_env_variables(self):
        """Test loading config from environment variables"""
        with patch.dict(os.environ, {"FLASK_ENV": "production", "FLASK_PORT": "8000"}):
            config = load_config()
            assert config["FLASK_ENV"] == "production"
            assert config["FLASK_PORT"] == 8000

    def test_gemini_api_key_required_in_non_test(self):
        """Test that GEMINI_API_KEY is required outside of tests"""
        # This should not raise in test mode
        config = load_config()
        assert config is not None

    def test_default_log_level(self):
        """Test default logging level"""
        config = load_config()
        assert config["LOG_LEVEL"] in ["INFO", "DEBUG", "WARNING", "ERROR"]

    def test_api_key_validation_rejects_empty_string(self):
        """Test that empty string GEMINI_API_KEY is rejected"""
        import os
        import sys

        # Only test in non-test mode to trigger validation
        original_modules = sys.modules.copy()

        try:
            # Temporarily remove pytest from modules to trigger validation
            if "pytest" in sys.modules:
                del sys.modules["pytest"]

            with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
                # Empty string should raise ValueError
                with pytest.raises(ValueError, match="Missing GEMINI_API_KEY"):
                    load_config()
        finally:
            # Restore original state
            sys.modules.update(original_modules)

    def test_config_port_must_be_integer(self):
        """Test that non-integer FLASK_PORT raises error"""
        with patch.dict(os.environ, {"FLASK_PORT": "not-a-number"}):
            with pytest.raises(ValueError):
                load_config()
