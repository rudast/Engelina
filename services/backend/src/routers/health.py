from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from src.database.session import engine


router = APIRouter(prefix='/api/v1/health', tags=['health'])


@router.get('/live')
async def liveness():
    return {'status': 'ok'}


@router.get('/ready')
async def readiness():
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        return {'status': 'ready'}
    except Exception as e:
        logging.getLogger(__name__).exception('Readiness check failed')
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={'status': 'unavailable', 'reason': str(e)},
        )
