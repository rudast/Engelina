from __future__ import annotations

from sqlalchemy.future import select
from src.database.models import Users
from src.database.session import async_session


async def get_user_by_id(tg_id: int):
    async with async_session() as sn:
        q = select(Users).where(Users.tg_id == tg_id)
        res = await sn.execute(q)
        return res.scalar_one_or_none()


async def create_user(tg_id: int):
    async with async_session() as session:
        user = Users(tg_id=tg_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
