# src/database/crud/stats.py
from __future__ import annotations

from datetime import datetime
from datetime import timedelta

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Achievements
from src.database.models import Errors
from src.database.models import Messages
from src.database.models import UserAchievements
from src.database.models import Users
from src.schemas.admin import AdminStats


async def get_basic_stats(session: AsyncSession) -> AdminStats:
    now = datetime.utcnow()
    last_5_min = now - timedelta(minutes=5)
    last_24h = now - timedelta(hours=24)

    q = select(func.count()).select_from(Users)
    total_users = int((await session.execute(q)).scalar_one() or 0)

    q = select(func.count()).select_from(
        Users,
    ).where(Users.last_seen_at >= last_5_min)
    online_users = int((await session.execute(q)).scalar_one() or 0)

    q = select(func.count()).select_from(Messages)
    total_messages = int((await session.execute(q)).scalar_one() or 0)

    q = select(func.count()).select_from(Errors)
    total_errors = int((await session.execute(q)).scalar_one() or 0)

    q = select(func.count()).select_from(Achievements)
    total_achievement_types = int(
        (await session.execute(q)).scalar_one()
        or 0,
    )

    q = select(func.count()).select_from(UserAchievements)
    total_awarded_achievements = int(
        (await session.execute(q)).scalar_one()
        or 0,
    )

    q = select(func.count()).select_from(
        Messages,
    ).where(Messages.created_at >= last_24h)
    messages_last_24h = int((await session.execute(q)).scalar_one() or 0)

    q = select(func.count()).select_from(
        Users,
    ).where(Users.created_at >= last_24h)
    new_users_last_24h = int((await session.execute(q)).scalar_one() or 0)

    avg_messages_per_user = 0
    if total_users > 0:
        avg_messages_per_user = total_messages // total_users

    return AdminStats(
        total_users=total_users,
        online_users=online_users,
        total_messages=total_messages,
        total_errors=total_errors,
        total_achievement_types=total_achievement_types,
        total_awarded_achievements=total_awarded_achievements,
        messages_last_24h=messages_last_24h,
        new_users_last_24h=new_users_last_24h,
        avg_messages_per_user=avg_messages_per_user,
    )
