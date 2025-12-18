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


def _map_error_type(type_str: str | None) -> ErrorTypeEnum:
    if not type_str:
        return ErrorTypeEnum.style

    t = type_str.strip().lower()

    if t in ('spelling', 'spell'):
        return ErrorTypeEnum.spelling
    if t in ('grammar',):
        return ErrorTypeEnum.grammar
    if t in ('punctuation', 'punct'):
        return ErrorTypeEnum.punctuation
    if t in ('style',):
        return ErrorTypeEnum.style
    if t in ('vocabulary', 'vocab'):
        return ErrorTypeEnum.vocabulary

    return ErrorTypeEnum.style


async def create_errors_bulk(
    session: AsyncSession,
    msg_id: int,
    items: Iterable[dict],
) -> list[Errors]:
    created: list[Errors] = []

    for it in items:
        if not isinstance(it, dict):
            continue

        type_raw = it.get('type') or it.get(
            'error_type',
        ) or it.get('errorType') or ''
        err_type = _map_error_type(type_raw)

        subtype = (it.get('subtype') or '').strip()

        original = (
            it.get('original')
            or it.get('user_text')
            or it.get('source')
            or ''
        ).strip()

        corrected = (
            it.get('corrected')
            or it.get('text_corrected')
            or ''
        ).strip()

        err = Errors(
            msg_id=msg_id,
            type=err_type,
            subtype=subtype,
            original=original,
            corrected=corrected,
        )
        session.add(err)
        created.append(err)

    if created:
        await session.flush()
        for e in created:
            await session.refresh(e)

    return created
