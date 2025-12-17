from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.user import get_tg_id_by_username
from src.database.deps import get_session
from src.schemas.auth import AuthRequest
from src.utils import send_notice

router = APIRouter(prefix='/api/v1/auth', tags=['auth'])


@router.post('/verify', status_code=status.HTTP_201_CREATED)
async def verify_user(
    data: AuthRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        tg_id = await get_tg_id_by_username(session, data.username)

        if tg_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found',
            )

        await send_notice(
            tg_id,
            f"""🔐 Authorization Code

Your authorization code is: {data.code}

Please use this code to sign in on the website.
Do not share this code with anyone.

If you didn’t request this, you can safely ignore this message.""",
        )
        return {
            'ok': True,
            'tg_id': tg_id,
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
