from __future__ import annotations

from redis import Redis
from rq import Queue

from src.settings import Settings


def get_redis(settings: Settings) -> Redis:
    return Redis.from_url(settings.REDIS_URL)


def get_queue(settings: Settings) -> Queue:
    redis = get_redis(settings=settings)
    return Queue(
        name=settings.RQ_QUEUE_NAME,
        connection=redis,
        default_timeout=getattr(settings, "JOB_TIMEOUT_S", 1800),
    )
