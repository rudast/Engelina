from __future__ import annotations

from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.database.models import Users


async def get_user_by_id(session: AsyncSession, tg_id: int) -> Users | None:
    q = select(Users).where(Users.tg_id == tg_id)
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def create_user(
    session: AsyncSession, tg_id: int,
    username: str,
) -> Users:
    user = Users(tg_id=tg_id, username=username)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def get_user_id_by_id(session: AsyncSession, tg_id: int) -> int | None:
    q = select(Users.id).where(Users.tg_id == tg_id)
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def get_list_of_users(session: AsyncSession) -> list[int]:
    q = select(Users.tg_id)
    res = await session.execute(q)
    return res.scalars().all()


async def update_user_last_seen(session: AsyncSession, user_id: int) -> None:
    stmt = (
        update(Users)
        .where(Users.id == user_id)
        .values(last_seen_at=datetime.utcnow())
    )
    await session.execute(stmt)
