from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Messages


async def create_message(
    session: AsyncSession,
    user_id: int,
    text_original: str,
    text_corrected: str,
    explanation: str,
    answer: str,
):
    msg = Messages(
        user_id=user_id,
        text_original=text_original,
        text_corrected=text_corrected,
        explanation=explanation,
        answer=answer,
    )
    session.add(msg)
    await session.flush()
    await session.refresh(msg)
    return msg
