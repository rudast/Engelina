# src/database/crud/stats.py
from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import Literal

from pydantic import BaseModel
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


Period = Literal['day', 'week', 'all']


class PeriodRange(BaseModel):
    start: datetime | None
    end: datetime


def _get_period_range(period: Period) -> PeriodRange:
    now = datetime.utcnow()
    if period == 'all':
        return PeriodRange(start=None, end=now)

    if period == 'day':
        start = now - timedelta(days=1)
        return PeriodRange(start=start, end=now)

    # period == "week"
    start = now - timedelta(days=7)
    return PeriodRange(start=start, end=now)


def _apply_period_filter(stmt, dt_column, pr: PeriodRange):
    if pr.start is None:
        return stmt
    return stmt.where(dt_column >= pr.start).where(dt_column <= pr.end)


async def get_user_id_by_username(
    session: AsyncSession,
    username: str,
) -> int | None:
    q = select(Users.id).where(Users.username == username)
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def get_messages_count(
    session: AsyncSession, user_id: int,
    period: Period,
) -> int:
    pr = _get_period_range(period)
    stmt = select(func.count(Messages.id))\
        .where(Messages.user_id == user_id)
    stmt = _apply_period_filter(stmt, Messages.created_at, pr)
    res = await session.execute(stmt)
    return int(res.scalar_one() or 0)


async def get_errors_count(
    session: AsyncSession, user_id: int,
    period: Period,
) -> int:
    pr = _get_period_range(period)
    stmt = (
        select(func.count(Errors.id))
        .select_from(Errors)
        .join(Messages, Messages.id == Errors.msg_id)
        .where(Messages.user_id == user_id)
    )
    stmt = _apply_period_filter(stmt, Messages.created_at, pr)
    res = await session.execute(stmt)
    return int(res.scalar_one() or 0)


async def get_errors_timeseries(
    session: AsyncSession, user_id: int,
    period: Period,
) -> list[dict]:
    pr = _get_period_range(period)

    day_col = func.date(Messages.created_at)

    msg_stmt = (
        select(day_col.label('day'), func.count(Messages.id).label('messages'))
        .where(Messages.user_id == user_id)
        .group_by(day_col)
        .order_by(day_col)
    )
    msg_stmt = _apply_period_filter(msg_stmt, Messages.created_at, pr)
    msg_res = await session.execute(msg_stmt)
    msg_rows = msg_res.all()

    err_stmt = (
        select(day_col.label('day'), func.count(Errors.id).label('errors'))
        .select_from(Messages)
        .join(Errors, Errors.msg_id == Messages.id)
        .where(Messages.user_id == user_id)
        .group_by(day_col)
        .order_by(day_col)
    )
    err_stmt = _apply_period_filter(err_stmt, Messages.created_at, pr)
    err_res = await session.execute(err_stmt)
    err_rows = err_res.all()

    msg_map = {str(r.day): int(r.messages) for r in msg_rows}
    err_map = {str(r.day): int(r.errors) for r in err_rows}

    days = sorted(set(msg_map.keys()) | set(err_map.keys()))
    out = []
    for d in days:
        out.append({
            'date': d,
            'errors': err_map.get(d, 0),
            'messages': msg_map.get(d, 0),
        })
    return out


async def get_errors_by_type(
    session: AsyncSession, user_id: int,
    period: Period,
) -> list[dict]:
    pr = _get_period_range(period)

    stmt = (
        select(Errors.type.label('type'), func.count(Errors.id).label('count'))
        .select_from(Errors)
        .join(Messages, Messages.id == Errors.msg_id)
        .where(Messages.user_id == user_id)
        .group_by(Errors.type)
        .order_by(func.count(Errors.id).desc())
    )
    stmt = _apply_period_filter(stmt, Messages.created_at, pr)
    res = await session.execute(stmt)

    return [{'type': str(r.type), 'count': int(r.count)} for r in res.all()]


async def get_achievements(
    session: AsyncSession, user_id:
    int, period: Period,
) -> list[dict]:
    pr = _get_period_range(period)

    stmt = (
        select(
            Achievements.code.label('code'),
            Achievements.title.label('title'),
            UserAchievements.earned_at.label('earned_at'),
        )
        .select_from(UserAchievements)
        .join(Achievements, Achievements.id == UserAchievements.achievement_id)
        .where(UserAchievements.user_id == user_id)
        .order_by(UserAchievements.earned_at.desc())
    )
    stmt = _apply_period_filter(stmt, UserAchievements.earned_at, pr)
    res = await session.execute(stmt)

    out = []
    for r in res.all():
        out.append({
            'code': str(r.code),
            'title': r.title,
            'earned_at': r.earned_at.date().isoformat(),
        })
    return out
