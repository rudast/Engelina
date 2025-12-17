from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    tg_id: int
    text_original: str


class MessageRead(BaseModel):
    id: int
    user_id: int
    text_original: str
    text_corrected: str
    explanation: str
    answer: str
    created_at: datetime

    model_config = {'from_attributes': True}
