from __future__ import annotations

import logging
import sys

from pydantic import ValidationError
from src.settings import DatabaseSettings
from src.settings import LoggingSettings


def load_settings() -> DatabaseSettings:
    try:
        settings = DatabaseSettings()
        logging.info('Successed to load URL from .env')
        return settings
    except ValidationError:
        logging.critical('Failed to load URL .env')
        sys.exit(1)


def setup_logging() -> logging.Logger:
    try:
        settings = LoggingSettings()
        logging.basicConfig(
            filename=settings.LOG_FILE,
            level=logging.INFO,
            format=settings.LOG_FORMAT,
        )
        return logging.getLogger()
    except ValidationError:
        print('Failed to load logging data from .env')
        sys.exit(1)
