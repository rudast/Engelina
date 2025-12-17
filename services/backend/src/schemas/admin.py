from __future__ import annotations

from pydantic import BaseModel


class AdminStats(BaseModel):
    total_users: int
    online_users: int
    total_messages: int
    total_errors: int
    total_achievement_types: int
    total_awarded_achievements: int
    messages_last_24h: int
    new_users_last_24h: int
    avg_messages_per_user: int
