from __future__ import annotations

from sqlalchemy.future import select
from src.database.models import Messages
from src.database.models import Users
from src.database.session import async_session


async def get_user_by_id(tg_id: int) -> Users | None:
    async with async_session() as sn:
        q = select(Users).where(Users.tg_id == tg_id)
        res = await sn.execute(q)
        return res.scalar_one_or_none()


async def create_user(tg_id: int, username: str) -> Users:
    async with async_session() as session:
        user = Users(tg_id=tg_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_user_id_by_tg_id(tg_id: int) -> int | None:
    async with async_session() as sn:
        q = select(Users.id).where(Users.tg_id == tg_id)
        res = await sn.execute(q)
        return res.scalar_one_or_none()


async def create_message(
    user_id: int,
    text_original: str,
    text_corrected: str,
    explanation: str,
    answer: str,
):
    async with async_session() as session:
        msg = Messages(
            user_id=user_id,
            text_original=text_original,
            text_corrected=text_corrected,
            explanation=explanation,
            answer=answer,
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg


async def get_list_of_users() -> list[int]:
    async with async_session() as session:
        q = select(Users.tg_id)
        res = await session.execute(q)
        return res.scalars().all()
