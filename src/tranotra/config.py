"""Configuration management for Tranotra Leads application"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Base configuration"""

    # Flask
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logging
    LOG_LEVEL = "INFO"

    # API Keys (from environment)
    GEMINI_API_KEY = None
    APOLLO_API_KEY = None
    HUNTER_API_KEY = None
    ALIYUN_ACCESS_KEY_ID = None
    ALIYUN_SECRET = None
    ALIYUN_FROM_EMAIL = None


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False


def load_config() -> dict:
    """Load configuration from environment variables

    Returns:
        dict: Configuration dictionary

    Raises:
        ValueError: If required environment variables are missing
    """
    # Determine which .env file to load
    if "pytest" in sys.modules:
        env_file = Path(".env.test")
        config_class = TestingConfig
    else:
        flask_env = os.getenv("FLASK_ENV", "development").lower()
        if flask_env == "production":
            config_class = ProductionConfig
        else:
            config_class = DevelopmentConfig

        # Try to load .env file
        env_file = Path(".env.local") if Path(".env.local").exists() else Path(".env.development")

    # Load .env file if it exists
    if env_file.exists():
        load_dotenv(env_file)

    # Load environment variables
    config = {
        "FLASK_ENV": os.getenv("FLASK_ENV", "development"),
        "FLASK_DEBUG": os.getenv("FLASK_DEBUG", "False").lower() == "true",
        "FLASK_HOST": os.getenv("FLASK_HOST", "0.0.0.0"),
        "FLASK_PORT": int(os.getenv("FLASK_PORT", "5000")),
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./data/tranotra_leads.db"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "APOLLO_API_KEY": os.getenv("APOLLO_API_KEY"),
        "HUNTER_API_KEY": os.getenv("HUNTER_API_KEY"),
        "ALIYUN_ACCESS_KEY_ID": os.getenv("ALIYUN_ACCESS_KEY_ID"),
        "ALIYUN_SECRET": os.getenv("ALIYUN_SECRET"),
        "ALIYUN_FROM_EMAIL": os.getenv("ALIYUN_FROM_EMAIL"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }

    # Validate required environment variables (only in non-test mode)
    if "pytest" not in sys.modules:
        # Validate GEMINI_API_KEY is set and non-empty
        if not (config["GEMINI_API_KEY"] and config["GEMINI_API_KEY"].strip()):
            raise ValueError(
                "Missing GEMINI_API_KEY. Please check .env file.\n"
                f"Expected file: {env_file}\n"
                "Create one from .env.example template.\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )

    return config


def create_app_config(app) -> None:
    """Apply configuration to Flask app

    Args:
        app: Flask application instance
    """
    flask_env = os.getenv("FLASK_ENV", "development").lower()

    if flask_env == "production":
        app.config.from_object(ProductionConfig)
    elif flask_env == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Load all configuration from environment and apply to app
    config_dict = load_config()
    for key, value in config_dict.items():
        # Apply all configuration keys to Flask app
        app.config[key] = value
