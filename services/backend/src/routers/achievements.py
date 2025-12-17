from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.achievement import get_user_achievements
from src.database.crud.user import get_user_id_by_id
from src.database.deps import get_session
from src.schemas.achievement import AchievementRead


router = APIRouter(prefix='/api/v1/achievements', tags=['achievements'])


@router.get(
    '/{tg_id}', response_model=AchievementRead,
    status_code=status.HTTP_200_OK,
)
async def get_achievement(
    tg_id: int, index: int = 0, session:
    AsyncSession = Depends(get_session),
):
    try:
        user_id = await get_user_id_by_id(session, tg_id)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='User not found',
            )

        row = await get_user_achievements(session, user_id, index)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='No achievements',
            )

        ach_id, title, description, earned_at, total = row
        return AchievementRead(
            id=ach_id,
            title=title,
            description=description,
            earned_at=earned_at,
            total=total,
            index=index % total,
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
