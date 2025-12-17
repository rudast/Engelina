from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from src.settings import Settings
from src.schemas import (
    ReplyRequest,
    ReplyResponse,
    FeedbackRequest,
    FeedbackResponse,
    ChatMessage,
    LanguageFeedback,
)
from .prompts import get_prompt
from .model import AIWorkerModel
from .utils import (
    Timer,
    trim_text,
    clamp_history,
    clamp_history_by_chars,
    safe_parse_language_feedback,
    fallback_language_feedback,
)

logger = logging.getLogger("ai_worker.service")

class AIWorkerService:

    def __init__(self, model: AIWorkerModel, settings: Settings):
        self.model = model
        self.settings = settings
        self._gen_sema = threading.Semaphore(settings.MAX_CONCURRENT_GENERATIONS)
    
    @staticmethod
    def _history_to_dicts(history: List[ChatMessage]) -> List[Dict[str, str]]:
        """
        Conver List[ChatMessage] to dict fromat expected by tokenizer
        """
        return [{"role": m.role, "content": m.content} for m in history]
    
    def make_reply(self, req: ReplyRequest, request_id: Optional[str] = None) -> ReplyResponse:
        """
        Generate conversation reply between user and worker
        """
        level = req.meta.level if req.meta else None
        system_prompt = get_prompt(level=level, kind="reply")

        user_msg = trim_text(req.message, self.settings.MAX_MESSAGE_CHARS)

        hist = clamp_history(req.history, max_turns=self.settings.MAX_HISTORY_TURNS)
        hist = clamp_history_by_chars(hist, max_total_chars=self.settings.MAX_HISTORY_CHARS)
        hist_dicts = self._history_to_dicts(hist)

        t = Timer.start()

        with self._gen_sema:
            reply_text = self.model.generate_reply(
                system_prompt=system_prompt,
                history=hist,
                user_message=user_msg,
            )

        latency = t.elapsed_ms()

        logger.info(
            "reply: ok | rid=%s user_id=%s session_id=%s level=%s latency=%s",
            request_id, req.user_id, req.session_id, level, latency
        )

        return ReplyResponse(
            reply=reply_text,
            meta={
                "latency_ms": latency,
                "mode": "reply",
                "level": level or "auto",
            },
        )
    def make_feedback(self, req: FeedbackRequest, request_id: Optional[str] = None) -> FeedbackResponse:
        """
        Generate structured language feedback about the user's last message.
        Must never crash the service if JSON formatting fails.
        """
        level = req.meta.level if req.meta else None
        system_prompt = get_prompt(level, kind="feedback")

        user_msg = trim_text(req.message, self.settings.MAX_MESSAGE_CHARS)

        t = Timer.start()
        with self._gen_sema:
            raw = self.model.generate_feedback_raw(
                system_prompt=system_prompt,
                user_message=user_msg,
            )
        latency = t.elapsed_ms()


        parsed: LanguageFeedback | None = safe_parse_language_feedback(raw)
        used_fallback = parsed is None

        if parsed is None:
            parsed = fallback_language_feedback(
                "Feedback temporarily unavailable (formatting error)."
            )
        if used_fallback is None:
            raw_preview = raw[:200].replace("\n", "\\n")
            logger.warning(
                "feedback fallback | rid=%s user_id=%s session_id=%s level=%s latency_ms=%s raw_preview=%s",
                request_id, req.user_id, req.session_id, level, latency, raw_preview
            )
        else:
            logger.info(
                "feedback ok | rid=%s user_id=%s session_id=%s level=%s latency_ms=%s items=%s",
                request_id, req.user_id, req.session_id, level, latency, len(parsed.items)
            )


        return FeedbackResponse(
            language_feedback=parsed,
            meta={
                "latency_ms": latency,
                "mode": "feedback",
                "level": level or "auto",
            },
        )