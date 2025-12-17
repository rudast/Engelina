from __future__ import annotations

from pydantic import BaseModel
from src.utils import ErrorTypeEnum


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
