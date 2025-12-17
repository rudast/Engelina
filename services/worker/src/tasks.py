from __future__ import annotations

import logging
import traceback
from typing import Any

from src.model import AIWorkerModel
from src.prompts import get_prompt
from src.settings import get_settings
from src.utils import fallback_language_feedback
from src.utils import safe_parse_language_feedback


_settings = get_settings()
_model: AIWorkerModel | None = None
logger = logging.getLogger('ai_worker.task')


def _get_model() -> AIWorkerModel:
    global _model
    if _model is None:
        _model = AIWorkerModel(_settings)
        _model.model.eval()
    return _model


def task_reply(*, level, history, message):
    logger.info('task reply: start')
    try:
        model = _get_model()
        logger.info('task reply: model loaded')

        system_prompt = get_prompt(level, kind='reply')
        reply_text = model.generate_reply(
            system_prompt=system_prompt, history=history, user_message=message,
        )
        logger.info('task reply: reply text generated')

        return {'reply': reply_text}
    except Exception as e:
        tb = traceback.format_exc()
        return {'error': str(e), 'traceback': tb}


def task_feedback(*, level: str | None, message: str) -> dict[str, Any]:
    model = _get_model()
    system_prompt = get_prompt(level, kind='feedback')
    raw = model.generate_feedback_raw(
        system_prompt=system_prompt, user_message=message,
    )
    logger.info('Model answer: %s', raw)
    print('Model answer: %s', raw)
    parsed = safe_parse_language_feedback(raw)
    print('Feedback parsed to %s', parsed)
    logger.info('Feedback parsed to %s', parsed)
    if parsed is None:
        parsed = fallback_language_feedback(
            'Feedback temporarily unavailable (formatting error).',
        )

    return {'language_feedback': parsed.model_dump()}
