from __future__ import annotations

from typing import Dict, List

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
    clamp_history,
    safe_parse_language_feedback,
    fallback_language_feedback,
)


class AIWorkerService:

    def __init__(self, model: AIWorkerModel, settings: Settings):
        self.model = model
        self.settings = settings
    
    @staticmethod
    def _history_to_dicts(history: List[ChatMessage]) -> List[Dict[str, str]]:
        """
        Conver List[ChatMessage] to dict fromat expected by tokenizer
        """
        return [{"role": m.role, "content": m.content} for m in history]
    
    def make_reply(self, req: ReplyRequest) -> ReplyResponse:
        """
        Generate conversation reply between user and worker
        """
        level = req.meta.level if req.meta else None
        system_prompt = get_prompt(level=level, kind="reply")

        hist = clamp_history(req.hystory, max_turns=self.settings.MAX_HISTORY_TURNS)
        hist_dicts = self._history_to_dicts(hist)

        t = Timer.start()
        reply_text = self.model.generate_reply(
            system_prompt=system_prompt,
            history=hist_dicts,
            user_message=req.message,
        )

        latency = t.elapsed_ms()

        return ReplyResponse(
            reply=reply_text,
            meta={
                "latency_ms": latency,
                "mode": "reply",
                "level": level or "auto",
            },
        )
    def make_feedback(self, req: FeedbackRequest) -> FeedbackResponse:
        """
        Generate structured language feedback about the user's last message.
        Must never crash the service if JSON formatting fails.
        """
        level = req.meta.level if req.meta else None
        system_prompt = get_prompt(level, kind="feedback")

        t = Timer.start()
        raw = self.model.generate_feedback_raw(
            system_prompt=system_prompt,
            user_message=req.message,
        )
        latency = t.elapsed_ms()

        parsed: LanguageFeedback | None = safe_parse_language_feedback(raw)
        if parsed is None:
            parsed = fallback_language_feedback(
                "Feedback temporarily unavailable (formatting error)."
            )

        return FeedbackResponse(
            language_feedback=parsed,
            meta={
                "latency_ms": latency,
                "mode": "feedback",
                "level": level or "auto",
            },
        )