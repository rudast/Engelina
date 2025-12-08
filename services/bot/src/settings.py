from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra='ignore',
    )


class BotSettings(BaseConfig):
    TOKEN: str


class LoggingSettings(BaseConfig):
    LOG_FILE: str
    LOG_FORMAT: str
