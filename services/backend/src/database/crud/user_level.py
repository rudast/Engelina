from __future__ import annotations

from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Users
from src.utils import LevelTypeEnum


async def check_user_code_and_get_tg(
    session: AsyncSession,
    username: str, code: str,
) -> int | None:

    q = select(Users.tg_id).where(
        Users.username ==
        username, Users.session_id == code,
    )
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def update_user_level_by_username(
    session: AsyncSession,
    username: str, new_level: LevelTypeEnum,
) -> Users | None:

    stmt = update(Users).where(Users.username == username).values(
        level=new_level,
    ).execution_options(synchronize_session='fetch')
    await session.execute(stmt)
    q = await session.execute(select(Users).where(Users.username == username))
    return q.scalar_one_or_none()


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> Users | None:
    q = select(Users).where(Users.username == username)
    res = await session.execute(q)
    return res.scalar_one_or_none()
