from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from src.utils import ErrorTypeEnum
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


class ErrorCreate(BaseModel):
    msg_id: int
    type: ErrorTypeEnum
    subtype: str
    original: str
    corrected: str


class ErrorRead(BaseModel):
    id: int
    msg_id: int
    type: ErrorTypeEnum
    subtype: str
    original: str
    corrected: str

    model_config = {'from_attributes': True}


class GetUsers(BaseModel):
    users: list[int] | None
