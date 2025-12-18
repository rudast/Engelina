from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.crud.error import create_errors_bulk
from src.database.crud.message import create_message
from src.database.crud.messages_with_awards import check_and_award_on_message
from src.database.crud.user import get_user_id_by_id
from src.database.crud.user import update_user_last_seen
from src.database.deps import get_session
from src.routers.users import create_user_endpoint
from src.schemas.message import MessageCreate
from src.schemas.message import MessageRead
from src.schemas.user import UserCreate
from src.utils import post_response
from src.utils import send_notice


router = APIRouter(prefix='/api/v1/messages', tags=['messages'])


@router.post(
    '', response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_message_endpoint(
    message: MessageCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        user_id = await get_user_id_by_id(session, message.tg_id)
        if user_id is None:
            await create_user_endpoint(UserCreate(tg_id=message.tg_id))
            user_id = await get_user_id_by_id(session, message.tg_id)

        reply_json = await post_response(
            url='http://ai_worker_api:8002/api/v1/worker/reply',
            data={
                'user_id': 'string',
                'session_id': 'string',
                'message': f"{message.text_original}",
                'history': [],
                'meta': {
                    'level': 'A2',
                    'platform': 'telegram',
                },
            },
        )

        feed_json = await post_response(
            url='http://ai_worker_api:8002/api/v1/worker/feedback',
            data={
                'user_id': 'string',
                'session_id': 'string',
                'message': f"{message.text_original}",
                'meta': {
                    'level': 'A2',
                    'platform': 'telegram',
                },
            },
        )
        logging.getLogger(__name__).info(feed_json)

        if user_id is None:
            return

        await update_user_last_seen(session, user_id)

        items = []
        try:
            items = feed_json.get('result', None).get(
                'language_feedback', {},
            ).get('items', [])
            if items is None:
                items = []
        except Exception:
            items = []

        corrected_text = ''
        explanation_text = ''
        if items:
            for it in items:
                tc = (
                    it.get('text_corrected') or it.get(
                        'corrected',
                    ) or ''
                ).strip()
                if tc:
                    corrected_text = tc
                    break

            explanations = []
            for idx, it in enumerate(items, start=1):
                field_expl = it.get('explanation') or it.get('message') or ''
                typ = it.get('type') or ''
                orig = it.get('original') or it.get('source') or ''
                corr = it.get('text_corrected') or it.get('corrected') or ''
                part = f"{idx}. {field_expl}".strip()
                if not field_expl:
                    part = f"{idx}. {typ} — original: {
                        orig
                    }; corrected: {corr}"
                explanations.append(part)
            explanation_text = '\n'.join(explanations)
        else:
            corrected_text = ''
            explanation_text = ''

        reply_text = ''
        try:
            reply_text = reply_json.get(
                'result',
                None,
            ).get('reply', '') or ''
        except Exception:
            reply_text = ''

        msg = await create_message(
            session,
            user_id, message.text_original, feed_json['result'][
                'language_feedback'
            ]['items'][0]['text_corrected'],
            feed_json['result']['language_feedback']
            ['items'][0]['explanation'],
            reply_text,
        )

        if items:
            await create_errors_bulk(session, msg.id, items)

        new_ach_ids = await check_and_award_on_message(session, user_id)
        if len(new_ach_ids) > 0:
            await send_notice(
                message.tg_id,
                """🎉 New Achievement Unlocked!
You’ve just earned a new achievement — great progress!
Use the /achievements command to see all your achievements.""",
            )

        if explanation_text:
            notify_parts = []
            if corrected_text:
                notify_parts.append(f"{corrected_text}")
            notify_parts.append(explanation_text)
            notify_message = '\n\n'.join(notify_parts)
            await send_notice(message.tg_id, notify_message)

        return msg

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Database not available.',
        )
