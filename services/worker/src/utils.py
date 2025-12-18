from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError
from rq.job import Job
from src.schemas import ChatMessage
from src.schemas import LanguageFeedback

log = logging.getLogger()


def trim_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ''
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + '...'


def clamp_history_by_chars(
        history: list[ChatMessage],
        max_total_chars,
) -> list[ChatMessage]:
    if max_total_chars <= 0:
        return []
    total = 0
    kept: list[ChatMessage] = []

    for msg in reversed(history):
        ln = len(msg.content)
        if total + ln > max_total_chars:
            break
        kept.append(msg)
        total += ln
    return list(reversed(kept))


@dataclass
class Timer:
    start_ms: int

    @staticmethod
    def start() -> Timer:
        return Timer(start_ms=int(time.time() * 1000))

    def elapsed_ms(self) -> int:
        return int(time.time() * 1000) - self.start_ms


def clamp_history(
        history: list[ChatMessage],
        max_turns: int,
) -> list[ChatMessage]:
    if max_turns <= 0:
        return []
    if len(history) <= max_turns:
        return history
    return history[-max_turns:]


def extract_json_object(text: str) -> dict[str, Any]:
    """
    extract json from text

    :param text: str
    :return: dict[str, Any]

    "some text ... {...valid_json...} ... some text"
    """
    if not text:
        raise ValueError('Empty text')

    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1 or end <= start:
        raise ValueError('No JSON object boundaries found')

    candidate = text[start: end + 1].strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decode failed: {e}") from e


def safe_parse_language_feedback(text: str) -> LanguageFeedback | None:
    try:
        obj = extract_json_object(text)

        lf = obj.get('language_feedback')
        if lf is None:
            log.error(
                "No 'language_feedback' key in object. Keys=%s",
                list(obj.keys()),
            )
            return None

        try:
            return LanguageFeedback.model_validate(lf)
        except ValidationError as e:
            log.error('LanguageFeedback validation failed:\n%s', e)
            log.error('Bad payload was:\n%s', lf)
            return None

    except Exception as e:
        log.exception('Failed to parse JSON from model output: %s', e)
        return None


def fallback_language_feedback(
        reason: str = 'Feedback temporarily unavailable.',
) -> LanguageFeedback:
    """
    Create a safe feedback object
    """
    return LanguageFeedback(items=[], overall_comment=reason)


async def wait_job_result(
        job: Job,
        *,
        timeout_s: int = 120,
        poll_s: float = 0.2,
):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        job.refresh()
        status = job.get_status()
        if status == 'finished':
            return job.result
        if status == 'failed':
            raise RuntimeError((job.exc_info or 'job failed')[-2000:])
        await asyncio.sleep(poll_s)
    raise TimeoutError('job timeout')

# def get_level_from_meta(meta: Meta) -> Optional[str]:
#     """
#     Helper to safely extract 'level'
#     """

#     if meta is None:
#         return None
#     level = getattr(meta, 'level', None)
#     if level:
#         return str(level)
#     if isinstance(meta, dict):
#         v = meta.get("level")
#         return str(v) if v else None
#     return None
