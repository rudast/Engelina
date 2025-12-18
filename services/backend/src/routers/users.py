from __future__ import annotations

from fastapi import APIRouter
from src.database.crud.user import create_message
from src.database.crud.user import create_user
from src.database.crud.user import get_user_by_id
from src.database.crud.user import get_user_id_by_tg_id
from src.schemas.user import MessageCreate
from src.schemas.user import MessageRead
from src.schemas.user import UserCreate
from src.schemas.user import UserRead


router = APIRouter()


@router.post('/start', response_model=UserRead)
async def start_user(user: UserCreate):
    db_user = await get_user_by_id(user.tg_id)
    if not db_user:
        db_user = await create_user(user.tg_id, user.username)

    return db_user


@router.post('/message', response_model=MessageRead)
async def send_message(message: MessageCreate):
    user_id = await get_user_id_by_tg_id(message.tg_id)
    if user_id is None:
        await start_user(UserCreate(tg_id=message.tg_id))
        user_id = await get_user_id_by_tg_id(message.tg_id)

    # TODO request to worker
    # TODO get corrected, explained text, answer

    msg = await create_message(user_id, message.text_original, '# TODO corrected', '# TODO explanation', '# TODO answer')
    return msg
