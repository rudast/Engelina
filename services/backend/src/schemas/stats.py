from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import Field


Period = Literal['day', 'week', 'all']


class ErrorTimePoint(BaseModel):
    date: str
    errors: int
    messages: int


class ErrorByType(BaseModel):
    type: str
    count: int


class AchievementOut(BaseModel):
    code: str
    title: str
    earned_at: str


class UserStatsResponse(BaseModel):
    period: str
    messages_count: int
    errors_count: int
    errors_per_message: float = Field(..., examples=[2.08])
    errors_timeseries: list[ErrorTimePoint]
    errors_by_type: list[ErrorByType]
    achievements: list[AchievementOut]
