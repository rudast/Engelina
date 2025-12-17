from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra='ignore',
        # env_file='.env'
    )


class DatabaseSettings(BaseConfig):
    DATABASE_URL: str


class LoggingSettings(BaseConfig):
    LOG_FILE: str
    LOG_FORMAT: str


class BotSettings(BaseConfig):
    TOKEN: str


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


@lru_cache
def get_logging_settings() -> LoggingSettings:
    return LoggingSettings()


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
