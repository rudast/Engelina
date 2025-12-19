from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.database.models import Base
from src.database.session import engine
from src.routers import achievements
from src.routers import admin
from src.routers import auth
from src.routers import health
from src.routers import history
from src.routers import leaderboard
from src.routers import messages
from src.routers import users


app = FastAPI()
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(health.router)
app.include_router(achievements.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(leaderboard.router)


@app.on_event('startup')
async def on_startup():
    logging.getLogger(__name__).info('Starting app')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
    except Exception:
        logging.getLogger(__name__).exception(
            'DB connection failed during startup',
        )
        raise


@app.on_event('shutdown')
async def on_shutdown():
    logging.getLogger(__name__).info('Shutting down app')
    await engine.dispose()


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, e: SQLAlchemyError):
    logging.getLogger(__name__).exception('Database error: %s', e)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            'error': 'database_error',
            'detail': 'Storage temporarily unavailable',
        },
    )
