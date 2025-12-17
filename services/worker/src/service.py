from __future__ import annotations

import logging
import threading

from src.schemas import ChatMessage
from src.schemas import FeedbackRequest
from src.schemas import FeedbackResponse
from src.schemas import LanguageFeedback
from src.schemas import ReplyRequest
from src.schemas import ReplyResponse
from src.settings import Settings

from .model import AIWorkerModel
from .prompts import get_prompt
from .utils import clamp_history
from .utils import clamp_history_by_chars
from .utils import fallback_language_feedback
from .utils import safe_parse_language_feedback
from .utils import Timer
from .utils import trim_text

logger = logging.getLogger('ai_worker.service')


class AIWorkerService:

    def __init__(self, model: AIWorkerModel, settings: Settings):
        self.model = model
        self.settings = settings
        self._gen_sema = threading.Semaphore(
            settings.MAX_CONCURRENT_GENERATIONS,
        )

    @staticmethod
    def _history_to_dicts(history: list[ChatMessage]) -> list[dict[str, str]]:
        """
        Conver List[ChatMessage] to dict fromat expected by tokenizer
        """
        return [{'role': m.role, 'content': m.content} for m in history]

    def make_reply(
            self,
            req: ReplyRequest,
            request_id: str | None = None,
    ) -> ReplyResponse:
        """
        Generate conversation reply between user and worker
        """
        level = req.meta.level if req.meta else None
        system_prompt = get_prompt(
            level=level,
            kind='reply',
        )

        user_msg = trim_text(req.message, self.settings.MAX_MESSAGE_CHARS)

        hist = clamp_history(
            req.history, max_turns=self.settings.MAX_HISTORY_TURNS,
        )
        hist = clamp_history_by_chars(
            hist, max_total_chars=self.settings.MAX_HISTORY_CHARS,
        )
        hist_dicts = self._history_to_dicts(hist)

        t = Timer.start()

        with self._gen_sema:
            reply_text = self.model.generate_reply(
                system_prompt=system_prompt,
                history=hist_dicts,
                user_message=user_msg,
            )

        latency = t.elapsed_ms()

        logger.info(
            'reply: ok | rid=%s user_id=%s session_id=%s level=%s latency=%s',
            request_id, req.user_id, req.session_id, level, latency,
        )

        return ReplyResponse(
            reply=reply_text,
            meta={
                'latency_ms': latency,
                'mode': 'reply',
                'level': level or 'auto',
            },
        )

    def make_feedback(
            self,
            req: FeedbackRequest,
            request_id: str | None = None,
    ) -> FeedbackResponse:
        """
        Generate structured language feedback about the user's last message.
        Must never crash the service if JSON formatting fails.
        """
        level = req.meta.level if req.meta else None
        system_prompt = get_prompt(level, kind='feedback')

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
                'Feedback temporarily unavailable (formatting error).',
            )
        if used_fallback is None:
            raw_preview = raw[:200].replace('\n', '\\n')
            rid_str = 'rid=' + request_id
            user_id_str = 'user_id=' + req.user_id
            session_id_str = 'session_id' + req.session_id
            level_str = 'level=' + level
            latency_str = 'latency_ms=' + latency
            raw_preview_str = 'raw_preview' + raw_preview

            logger.warning(
                rid_str + user_id_str + session_id_str +
                level_str + latency_str + raw_preview_str,
            )
        else:
            logger.info(
                'feedback ok | rid=%s user_id=%s session_id=%s \
                    level=%s latency_ms=%s items=%s',
                request_id, req.user_id, req.session_id, level, latency, len(
                    parsed.items,
                ),
            )

        return FeedbackResponse(
            language_feedback=parsed,
            meta={
                'latency_ms': latency,
                'mode': 'feedback',
                'level': level or 'auto',
            },
        )
