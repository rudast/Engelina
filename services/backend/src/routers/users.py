from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.user import create_user
from src.database.crud.user import get_list_of_users
from src.database.crud.user import get_user_by_id
from src.database.deps import get_session
from src.schemas.user import GetUsers
from src.schemas.user import UserCreate
from src.schemas.user import UserRead


router = APIRouter(prefix='/api/v1/users', tags=['users'])


@router.post('/', response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user: UserCreate, session: AsyncSession =
    Depends(get_session),
):
    try:
        db_user = await get_user_by_id(session, user.tg_id)
        if not db_user:
            db_user = await create_user(session, user.tg_id, user.username)

        return db_user
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )


@router.get('/', response_model=GetUsers, status_code=status.HTTP_200_OK)
async def get_users_endpoint(session: AsyncSession = Depends(get_session)):
    try:
        users = await get_list_of_users(session)
        return GetUsers(users=users)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
