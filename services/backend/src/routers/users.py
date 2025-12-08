from __future__ import annotations

from fastapi import APIRouter
from src.database.crud.user import create_user
from src.database.crud.user import get_user_by_id
from src.schemas.user import UserCreate
from src.schemas.user import UserRead


router = APIRouter()


@router.post('/start', response_model=UserRead)
async def start_user(user: UserCreate):
    db_user = await get_user_by_id(user.tg_id)
    if not db_user:
        db_user = await create_user(user.tg_id)

    return db_user
