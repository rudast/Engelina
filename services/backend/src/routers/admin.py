from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.stats import get_basic_stats
from src.database.deps import get_session
from src.schemas.admin import AdminStats


router = APIRouter(prefix='/api/v1/admin', tags=['admin'])


@router.get(
    '/stats', response_model=AdminStats,
    status_code=status.HTTP_200_OK,
)
async def get_stats_endpoint(session: AsyncSession = Depends(get_session)):
    try:
        stats = await get_basic_stats(session)
        return stats
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
