from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from src.settings import get_database_settings


settings = get_database_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False,
)
Base = declarative_base()
