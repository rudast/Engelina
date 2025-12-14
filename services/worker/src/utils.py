from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from src.schemas import ChatMessage, LanguageFeedback, Meta

@dataclass
class Timer:
    start_ms: int

    @staticmethod
    def start() -> "Timer":
        return Timer(start_ms=int(time.time() * 1000))
    
    def elapsed_ms(self) -> int:
        return int(time.time() * 1000) - self.start_ms
    

def clamp_history(history: list[ChatMessage], max_turns: int) -> list[ChatMessage]:
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

    Работает даже если текст вида "some text ... {...valid_json...} ... some text"
    """
    if not text:
        raise ValueError("Empty text")
    
    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object boundaries found")
    
    candidate = text[start: end + 1].strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decode failed: {e}") from e
    

def safe_parse_language_feedback(text: str) -> Optional[LanguageFeedback]:
    """
    Try to parse model output us language feedback
    
    :param text: str
    :return: LanguageFeedback
    """
    try: 
        obj = extract_json_object()

        lf = obj.get('language_feedback')
        if lf is None:
            return None
        return LanguageFeedback.model_validate(lf)
    except Exception:
        return None
    

def fallback_language_feedback(reason: str = "Feedback temporarily unavailable.") -> LanguageFeedback:
    """
    Create a safe feedback object
    """
    return LanguageFeedback(items=[], overall_comment=reason)


# def get_level_from_meta(meta: Meta) -> Optional[str]:
#     """
#     Helper to safely extract 'level' from meta if meta may be None/dict/pydantic
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