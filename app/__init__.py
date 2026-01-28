"""CaseLoad application factory."""

import logging
import os
import sys

from flask import Flask

from app.config import config
from app.extensions import db


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: Configuration name ('development', 'production', 'testing').
                    Defaults to FLASK_ENV environment variable or 'development'.

    Returns:
        Configured Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    # Configure logging
    _configure_logging(app)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Import models so they are registered with SQLAlchemy
    from app import models  # noqa: F401

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    _register_blueprints(app)

    return app


def _configure_logging(app: Flask) -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if app.debug else logging.INFO

    # Configure root logger for our modules
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Set log levels for our modules
    for module in ["data.sources", "data.sync", "app.blueprints"]:
        logging.getLogger(module).setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("jira").setLevel(logging.WARNING)


def _register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.blueprints.main import bp as main_bp
    from app.blueprints.trends import bp as trends_bp
    from app.blueprints.impact import bp as impact_bp
    from app.blueprints.api import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(trends_bp, url_prefix="/trends")
    app.register_blueprint(impact_bp, url_prefix="/impact")
    app.register_blueprint(api_bp, url_prefix="/api")
