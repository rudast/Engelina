from __future__ import annotations

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    username: str | None
    value: int
    user_id: int


class LeaderboardResponse(BaseModel):
    category: str
    entries: list[LeaderboardEntry]
    current_index: int
    total_categories: int
