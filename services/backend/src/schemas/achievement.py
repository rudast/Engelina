from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AchievementRead(BaseModel):
    id: int
    title: str
    description: str
    earned_at: datetime
    total: int
    index: int
