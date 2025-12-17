from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Messages


async def get_last_messages_by_user_id(
    session: AsyncSession,
    user_id: int,
    limit: int = 18,
) -> list[Messages]:
    q = (
        select(Messages)
        .where(Messages.user_id == user_id)
        .order_by(Messages.created_at.desc())
        .limit(limit)
    )
    res = await session.execute(q)
    return res.scalars().all()
