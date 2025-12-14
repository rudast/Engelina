# src/settings.py
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MODEL_ID: str = "Qwen/Qwen2.5-7B-Instruct"
    DEVICE: Optional[str] = None
    LOAD_IN_4BIT: bool = True

    MAX_NEW_TOKENS_REPLY: int = 192
    MAX_NEW_TOKENS_FEEDBACK: int = 256
    TEMPERATURE_REPLY: float = 0.6
    TEMPERATURE_FEEDBACK: float = 0.3
    TOP_P: float = 0.9

    MAX_HISTORY_TURNS: int = 16
    LOG_LEVEL: str = "INFO"
    HF_CACHE_DIR: Optional[str] = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
