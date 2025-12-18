from __future__ import annotations

import logging

from redis import Redis
from rq import Queue
from src.settings import Settings

logger = logging.getLogger('ai_worker.queue')


def get_redis(settings: Settings) -> Redis:
    logger.info('redis: connect | url=%s', settings.REDIS_URL)
    r = Redis.from_url(settings.REDIS_URL)
    return r


def get_queue(settings: Settings) -> Queue:
    redis = get_redis(settings=settings)
    q = Queue(
        name=settings.RQ_QUEUE_NAME,
        connection=redis,
        default_timeout=getattr(settings, 'JOB_TIMEOUT_S', 1800),
    )
    logger.info(
        'rq queue: ready | name=%s default_timeout_s=%s',
        settings.RQ_QUEUE_NAME,
        getattr(settings, 'JOB_TIMEOUT_S', 1800),
    )
    return q
