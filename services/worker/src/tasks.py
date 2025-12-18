from __future__ import annotations

import logging
import traceback
from functools import lru_cache

from src.model import AIWorkerModel
from src.prompts import get_prompt
from src.service import AIWorkerService
from src.settings import get_settings
from src.utils import fallback_language_feedback
from src.utils import safe_parse_language_feedback

logger = logging.getLogger('ai_worker.tasks')


@lru_cache(maxsize=1)
def get_service() -> AIWorkerService:
    settings = get_settings()
    logger.info(
        'service cache: init | model_id=%s load_in_4bit=%s',
        settings.MODEL_ID,
        settings.LOAD_IN_4BIT,
    )

    model = AIWorkerModel(settings)
    model.model.eval()

    svc = AIWorkerService(model=model, settings=settings)
    logger.info('service cache: ready')
    return svc


def task_reply(level: str | None, history: list[dict], message: str):
    logger.info(
        'task_reply: start | level=%s hist_turns=%s msg_len=%s',
        level,
        len(history),
        len(message or ''),
    )
    try:
        svc = get_service()
        system_prompt = get_prompt(level, kind='reply')

        reply_text = svc.model.generate_reply(
            system_prompt=system_prompt,
            history=history,
            user_message=message,
        )

        logger.info('task_reply: ok | reply_len=%s', len(reply_text or ''))
        return {'reply': reply_text}

    except Exception as e:
        logger.exception('task_reply: error | err=%s', e)
        tb = traceback.format_exc()
        return {'error': str(e), 'traceback': tb}


def task_feedback(level: str | None, message: str):
    logger.info(
        'task_feedback: start | level=%s msg_len=%s',
        level,
        len(message or ''),
    )
    try:
        svc = get_service()
        system_prompt = get_prompt(level, kind='feedback')

        raw = svc.model.generate_feedback_raw(
            system_prompt=system_prompt,
            user_message=message,
        )

        raw_preview = (raw or '')[:300].replace('\n', '\\n')
        logger.info(
            'task_feedback: model_output_preview | preview=%s', raw_preview,
        )

        parsed = safe_parse_language_feedback(raw)

        if parsed is None:
            logger.warning('task_feedback: parse failed -> fallback used')
            parsed = fallback_language_feedback(
                'Feedback temporarily unavailable (formatting error).',
            )
        else:
            logger.info(
                'task_feedback: parsed ok | items=%s',
                len(parsed.items),
            )

        return {'language_feedback': parsed.model_dump()}

    except Exception as e:
        logger.exception('task_feedback: error | err=%s', e)
        tb = traceback.format_exc()
        return {'error': str(e), 'traceback': tb}
