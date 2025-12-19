from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.leaderboard import get_top_users_by_achievements
from src.database.crud.leaderboard import get_top_users_by_errors
from src.database.crud.leaderboard import get_top_users_by_messages
from src.database.deps import get_session
from src.schemas.leaderboard import LeaderboardResponse


router = APIRouter(prefix='/api/v1/leaderboard', tags=['leaderboard'])

CATEGORIES = ['messages', 'errors', 'achievements']


@router.get('/{category_index}', response_model=LeaderboardResponse)
async def get_leaderboard(
    category_index: int,
    session: AsyncSession = Depends(get_session),
):
    if not 0 <= category_index < len(CATEGORIES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid category index',
        )

    category = CATEGORIES[category_index]

    try:
        if category == 'messages':
            entries = await get_top_users_by_messages(session, limit=10)
        elif category == 'errors':
            entries = await get_top_users_by_errors(session, limit=10)
        elif category == 'achievements':
            entries = await get_top_users_by_achievements(session, limit=10)

        return LeaderboardResponse(
            category=category,
            entries=[
                {
                    'username': user.username,
                    'value': value,
                    'user_id': user.tg_id,
                }
                for user, value in entries
            ],
            current_index=category_index,
            total_categories=len(CATEGORIES),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {str(e)}",
        )
