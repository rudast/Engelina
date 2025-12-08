from __future__ import annotations

from fastapi import FastAPI
from src.database.models import Base
from src.database.session import engine
from src.routers import users


app = FastAPI()
app.include_router(users.router, prefix='/users')


@app.on_event('startup')
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
