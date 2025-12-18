from __future__ import annotations

import logging
import os
import sys


def setup_logging(level: str | None = None) -> None:
    """
    Central logging setup for the whole service.
    - One-line logs to stdout (docker-friendly)
    - Makes uvicorn/fastapi logs consistent too
    """
    lvl = (level or os.getenv('LOG_LEVEL') or 'INFO').upper()
    numeric = getattr(logging, lvl, logging.INFO)

    fmt = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'

    # Force reconfigure root logger (important for uvicorn workers)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(numeric)

    h = logging.StreamHandler(sys.stdout)
    h.setLevel(numeric)
    h.setFormatter(logging.Formatter(fmt))
    root.addHandler(h)

    # Align common server loggers
    for name in (
        'uvicorn', 'uvicorn.error',
        'uvicorn.access', 'fastapi', 'rq',
    ):
        logging.getLogger(name).setLevel(numeric)

    logging.getLogger(__name__).info('logging configured | level=%s', lvl)
