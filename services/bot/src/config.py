from __future__ import annotations

import logging
import sys

from pydantic import ValidationError
from settings import get_bot_settings
from settings import get_log_settings


def load_settings():
    try:
        get_bot_settings()
        logging.info('Successed to load token from .env')
    except ValidationError:
        logging.critical('Failed to load token .env')
        sys.exit(1)


def setup_logging():
    try:
        settings = get_log_settings()
        logging.basicConfig(
            filename=settings.LOG_FILE,
            level=logging.INFO,
            format=settings.LOG_FORMAT,
        )
    except ValidationError:
        print('Failed to load logging data from .env')
        sys.exit(1)
