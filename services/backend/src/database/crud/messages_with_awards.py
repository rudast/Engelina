from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.achievement import award_achievement_by_code
from src.database.crud.achievement import get_errors_count
from src.database.crud.achievement import get_messages_count
from src.database.crud.achievement import get_total_achievements_count
from src.database.crud.achievement import get_user_achievement_codes
from src.database.crud.achievement import get_user_achievements_count

MESSAGE_THRESHOLDS = {
    1: 1,
    2: 20,
    3: 100,
    4: 1000,
}

ERROR_THRESHOLDS = {
    5: 1,
    6: 10,
    7: 100,
}

META_CODES = {
    'first_any': 9,
    'collector': 10,
    'completionist': 11,
}


async def check_and_award_on_message(
    session: AsyncSession,
    user_id: int,
) -> list[int]:
    awarded: list[int] = []

    messages_count = await get_messages_count(session, user_id)
    errors_count = await get_errors_count(session, user_id)

    existing_codes = await get_user_achievement_codes(session, user_id)

    for code, threshold in MESSAGE_THRESHOLDS.items():
        if messages_count >= threshold and code not in existing_codes:
            ach_id = await award_achievement_by_code(session, user_id, code)
            if ach_id:
                awarded.append(ach_id)

    for code, threshold in ERROR_THRESHOLDS.items():
        if errors_count >= threshold and code not in existing_codes:
            ach_id = await award_achievement_by_code(session, user_id, code)
            if ach_id:
                awarded.append(ach_id)

    if awarded:
        existing_codes = await get_user_achievement_codes(session, user_id)

    user_ach_count = await get_user_achievements_count(session, user_id)

    if user_ach_count >= 1 and META_CODES['first_any'] not \
            in existing_codes:
        ach_id = await award_achievement_by_code(
            session, user_id,
            META_CODES['first_any'],
        )
        if ach_id:
            awarded.append(ach_id)
            existing_codes.add(META_CODES['first_any'])
            user_ach_count += 1

    if user_ach_count >= 5 and META_CODES['collector'] not \
            in existing_codes:
        ach_id = await award_achievement_by_code(
            session, user_id,
            META_CODES['collector'],
        )
        if ach_id:
            awarded.append(ach_id)
            existing_codes.add(META_CODES['collector'])
            user_ach_count += 1

    total_ach = await get_total_achievements_count(session)
    if user_ach_count >= total_ach and META_CODES['completionist'] not \
            in existing_codes and total_ach > 0:
        ach_id = await award_achievement_by_code(
            session, user_id,
            META_CODES['completionist'],
        )
        if ach_id:
            awarded.append(ach_id)

    return awarded
