from __future__ import annotations

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    REDIS_URL: str = "redis://redis:6379/0"
    RQ_QUEUE_NAME: str = "ai_worker"
    RQ_RESULT_TTL_S: int = 3600

    LOG_LEVEL: str = "INFO"

    MODEL_ID: str = "Qwen/Qwen2.5-7B-Instruct"
    DEVICE: Optional[str] = None
    LOAD_IN_4BIT: bool = True

    MAX_HISTORY_TURNS: int = 16
    MAX_MESSAGE_CHARS: int = 1200
    MAX_HISTORY_CHARS: int = 8000
    MAX_CONCURRENT_GENERATIONS: int = 1
    MAX_NEW_TOKENS_REPLY: int = 128
    MAX_NEW_TOKENS_FEEDBACK: int = 128
    TEMPERATURE_REPLY: float = 0.6
    TEMPERATURE_FEEDBACK: float = 0.1
    TOP_P: float = 0.9



@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()