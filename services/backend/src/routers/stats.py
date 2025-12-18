from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.stats import get_achievements
from src.database.crud.stats import get_errors_by_type
from src.database.crud.stats import get_errors_count
from src.database.crud.stats import get_errors_timeseries
from src.database.crud.stats import get_messages_count
from src.database.crud.stats import get_user_id_by_username
from src.database.deps import get_session
from src.schemas.stats import UserStatsResponse

Period = Literal['day', 'week', 'all']

router = APIRouter(prefix='/api/v1/stats', tags=['stats'])


@router.get(
    '/', response_model=UserStatsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_stats(
    tg_username: str = Query(
        ...,
        description='Telegram username, например: name',
    ),
    period: Period = Query('week', description='day|week|all'),
    session: AsyncSession = Depends(get_session),
):
    try:
        user_id = await get_user_id_by_username(session, tg_username)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found',
            )

        messages_count = await get_messages_count(session, user_id, period)
        errors_count = await get_errors_count(session, user_id, period)

        errors_per_message = 0.0
        if messages_count > 0:
            errors_per_message = round(errors_count / messages_count, 2)

        timeseries = await get_errors_timeseries(session, user_id, period)
        by_type = await get_errors_by_type(session, user_id, period)
        achievements = await get_achievements(session, user_id, period)

        return {
            'period': period,
            'messages_count': messages_count,
            'errors_count': errors_count,
            'errors_per_message': errors_per_message,
            'errors_timeseries': timeseries,
            'errors_by_type': by_type,
            'achievements': achievements,
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
