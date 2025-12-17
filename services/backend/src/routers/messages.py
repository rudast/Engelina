from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.message import create_message
from src.database.crud.messages_with_awards import check_and_award_on_message
from src.database.crud.user import get_user_id_by_id
from src.database.crud.user import update_user_last_seen
from src.database.deps import get_session
from src.routers.users import create_user_endpoint
from src.schemas.message import MessageCreate
from src.schemas.message import MessageRead
from src.schemas.user import UserCreate
from src.utils import send_notice

router = APIRouter(prefix='/api/v1/messages', tags=['messages'])


@router.post(
    '', response_model=MessageRead, status_code=status.HTTP_201_CREATED,
)
async def create_message_endpoint(
    message: MessageCreate, session:
    AsyncSession = Depends(get_session),
):
    try:
        user_id = await get_user_id_by_id(session, message.tg_id)
        if user_id is None:
            await create_user_endpoint(UserCreate(tg_id=message.tg_id))
            user_id = await get_user_id_by_id(session, message.tg_id)

        # TODO request to worker
        # TODO get corrected, explained text, answer

        if user_id is None:
            return

        await update_user_last_seen(session, user_id)

        msg = await create_message(
            session,
            user_id, message.text_original, '# TODO corrected',
            '# TODO explanation', '# TODO answer',
        )

        new_ach_ids = await check_and_award_on_message(session, user_id)
        if len(new_ach_ids) > 0:
            # TODO notice user
            await send_notice(
                message.tg_id,
                """🎉 New Achievement Unlocked!
You’ve just earned a new achievement — great progress!
Use the /achievements command to see all your achievements.""",
            )

        return msg
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
