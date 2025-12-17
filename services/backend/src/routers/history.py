from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.history import get_last_messages_by_user_id
from src.database.crud.user_level import get_user_by_username
from src.database.deps import get_session
from src.schemas.chat import ChatMessage

router = APIRouter(prefix='/api/v1', tags=['history'])


@router.get(
    '/history/{username}', response_model=list[ChatMessage],
    status_code=status.HTTP_201_CREATED,
)
async def get_chat_history(
    username: str, session: AsyncSession =
    Depends(get_session), limit: int = 18,
):
    try:
        user = await get_user_by_username(session, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='User not found',
            )

        msgs = await get_last_messages_by_user_id(
            session, user.id,
            limit=limit,
        )

        msgs.reverse()

        out: list[ChatMessage] = []
        for m in msgs:
            if m.text_original:
                out.append(ChatMessage(role='user', content=m.text_original))
            if m.answer:
                out.append(ChatMessage(role='assistant', content=m.answer))

        return out
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
