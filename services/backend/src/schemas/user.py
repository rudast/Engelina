from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from src.utils import LevelTypeEnum


class UserCreate(BaseModel):
    tg_id: int
    username: str


class UserUpdate(BaseModel):
    tg_id: int
    level: LevelTypeEnum


class UserRead(BaseModel):
    id: int
    tg_id: int
    username: str
    session_id: str
    level: LevelTypeEnum
    created_at: datetime
    last_seen_at: datetime

    model_config = {'from_attributes': True}


class GetUsers(BaseModel):
    users: list[int] | None


class UserLevelUpdate(BaseModel):
    level: LevelTypeEnum
