from __future__ import annotations

import logging
import sys

from pydantic import ValidationError
from settings import BotSettings
from settings import LoggingSettings


def load_settings() -> BotSettings:
    try:
        settings = BotSettings()
        logging.info('Successed to load token from .env')
        return settings
    except ValidationError:
        logging.critical('Failed to load token .env')
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
