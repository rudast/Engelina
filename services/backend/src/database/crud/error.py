from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Errors
from src.utils import ErrorTypeEnum


async def create_error(
    session: AsyncSession,
    msg_id: int,
    error_type: ErrorTypeEnum,
    subtype: str | None = None,
    original: str | None = None,
    corrected: str | None = None,
) -> Errors:
    err = Errors(
        msg_id=msg_id,
        type=error_type,
        subtype=subtype or '',
        original=original or '',
        corrected=corrected or '',
    )
    session.add(err)
    await session.flush()
    await session.refresh(err)
    return err


async def create_errors_bulk(
    session: AsyncSession,
    errors_data: Iterable[dict],
) -> list[Errors]:
    created: list[Errors] = []
    for d in errors_data:
        err = Errors(
            msg_id=d['msg_id'],
            type=d['error_type'],
            subtype=d.get('subtype', '') or '',
            original=d.get('original', '') or '',
            corrected=d.get('corrected', '') or '',
        )
        session.add(err)
        created.append(err)
    await session.flush()
    for e in created:
        await session.refresh(e)
    return created
