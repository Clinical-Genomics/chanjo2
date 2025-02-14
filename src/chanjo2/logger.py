import logging

import coloredlogs
from fastapi.applications import FastAPI


def configure_log(log: logging.Logger, app: FastAPI):
    """Configure logging."""

    current_log_level = log.getEffectiveLevel()
    logging.getLogger("sqlalchemy.engine.Engine").disabled = True
    coloredlogs.install(level="DEBUG" if app.debug else current_log_level)
