from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra='ignore',
        # env_file='.env'
    )


class BotSettings(BaseConfig):
    TOKEN: str
    ADMINS: list[int]


class LoggingSettings(BaseConfig):
    LOG_FILE: str
    LOG_FORMAT: str


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()


@lru_cache
def get_log_settings() -> LoggingSettings:
    return LoggingSettings()
