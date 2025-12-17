from __future__ import annotations

import logging
import sys

from pydantic import ValidationError
from src.settings import get_database_settings
from src.settings import get_logging_settings


def load_settings() -> None:
    try:
        get_database_settings()
        logging.info('Successed to load URL from .env')
    except ValidationError:
        logging.critical('Failed to load URL .env')
        sys.exit(1)


def setup_logging() -> None:
    try:
        settings = get_logging_settings()
        logging.basicConfig(
            filename=settings.LOG_FILE,
            level=logging.INFO,
            format=settings.LOG_FORMAT,
        )
    except ValidationError:
        print('Failed to load logging data from .env')
        sys.exit(1)
