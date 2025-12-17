from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Achievements
from src.database.models import Errors
from src.database.models import Messages
from src.database.models import UserAchievements


async def get_user_achievements(
    session: AsyncSession,
    user_id: int,
    index: int = 0,
) -> tuple[int, str, str, datetime, int] | None:
    total_q = select(func.count()).select_from(
        UserAchievements,
    ).where(UserAchievements.user_id == user_id)
    total_res = await session.execute(total_q)
    total = total_res.scalar_one()
    if total == 0:
        return None

    norm_index = index % total

    stmt = (
        select(
            Achievements.id,
            Achievements.title,
            Achievements.description,
            UserAchievements.earned_at,
        )
        .join(
            UserAchievements, UserAchievements.achievement_id
            == Achievements.id,
        )
        .where(UserAchievements.user_id == user_id)
        .order_by(UserAchievements.earned_at)
        .offset(norm_index)
        .limit(1)
    )
    res = await session.execute(stmt)
    row = res.first()
    if row is None:
        return None

    ach_id, title, description, earned_at = row
    return (ach_id, title, description, earned_at, total)


async def get_messages_count(session: AsyncSession, user_id: int) -> int:
    q = select(func.count()).select_from(
        Messages,
    ).where(Messages.user_id == user_id)
    res = await session.execute(q)
    return int(res.scalar_one() or 0)


async def get_errors_count(session: AsyncSession, user_id: int) -> int:
    q = (
        select(func.count())
        .select_from(Errors)
        .join(Messages, Messages.id == Errors.msg_id)
        .where(Messages.user_id == user_id)
    )
    res = await session.execute(q)
    return int(res.scalar_one() or 0)


async def get_user_achievement_codes(
    session: AsyncSession,
    user_id: int,
) -> set[int]:
    q = (
        select(Achievements.code)
        .select_from(Achievements)
        .join(
            UserAchievements, UserAchievements.achievement_id ==
            Achievements.id,
        )
        .where(UserAchievements.user_id == user_id)
    )
    res = await session.execute(q)
    rows = res.scalars().all()
    return set(rows)


async def award_achievement_by_code(
    session: AsyncSession, user_id:
    int, code: int,
) -> int | None:
    q = select(Achievements).where(Achievements.code == code)
    r = await session.execute(q)
    ach = r.scalar_one_or_none()
    if ach is None:
        return None

    q2 = select(func.count()).select_from(UserAchievements).where(
        UserAchievements.user_id == user_id,
        UserAchievements.achievement_id == ach.id,
    )
    r2 = await session.execute(q2)
    if int(r2.scalar_one() or 0) > 0:
        return None

    ua = UserAchievements(user_id=user_id, achievement_id=ach.id)
    session.add(ua)
    await session.flush()
    return ach.id


async def get_user_achievements_count(
    session: AsyncSession,
    user_id: int,
) -> int:
    q = select(func.count()).select_from(UserAchievements).where(
        UserAchievements.user_id == user_id,
    )
    res = await session.execute(q)
    return int(res.scalar_one() or 0)


async def get_total_achievements_count(session: AsyncSession) -> int:
    q = select(func.count()).select_from(Achievements)
    res = await session.execute(q)
    return int(res.scalar_one() or 0)
