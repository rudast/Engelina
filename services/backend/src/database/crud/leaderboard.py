from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Errors
from src.database.models import Messages
from src.database.models import UserAchievements
from src.database.models import Users


async def get_top_users_by_messages(session: AsyncSession, limit: int = 10):
    stmt = (
        select(Users, func.count(Messages.id).label('count'))
        .join(Messages, Users.id == Messages.user_id)
        .group_by(Users.id)
        .order_by(func.count(Messages.id).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.all()


async def get_top_users_by_errors(session: AsyncSession, limit: int = 10):
    stmt = (
        select(Users, func.count(Errors.id).label('count'))
        .join(Messages, Users.id == Messages.user_id)
        .join(Errors, Messages.id == Errors.msg_id)
        .group_by(Users.id)
        .order_by(func.count(Errors.id).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.all()


async def get_top_users_by_achievements(
    session: AsyncSession,
    limit: int = 10,
):
    stmt = (
        select(Users, func.count(UserAchievements.id).label('count'))
        .join(UserAchievements, Users.id == UserAchievements.user_id)
        .group_by(Users.id)
        .order_by(func.count(UserAchievements.id).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.all()
