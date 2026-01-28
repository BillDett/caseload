"""Application configuration classes."""

import os
from pathlib import Path


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).parent.parent / 'instance' / 'caseload.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Jira settings
    JIRA_SERVER = os.environ.get("JIRA_SERVER", "")
    JIRA_USERNAME = os.environ.get("JIRA_USERNAME", "")
    JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

    # Analytics settings
    DEFAULT_SLA_DAYS = int(os.environ.get("DEFAULT_SLA_DAYS", "30"))


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
