from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


# Class for feedback and reply

class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class Meta(BaseModel):
    level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] | None = 'A2'
    platform: Literal['telegram', 'web']


class ReplyRequest(BaseModel):
    user_id: str
    session_id: str | None
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    meta: Meta | None = None


class ReplyResponse(BaseModel):
    # user_id: str
    reply: str
    meta: dict | None = None


class FeedbackItem(BaseModel):
    user_text: str
    error_type: Literal[
        'grammar', 'spelling',
        'punctuation', 'style', 'vocabulary',
    ]
    explanation: str
    text_corrected: str | None


class LanguageFeedback(BaseModel):
    items: list[FeedbackItem]
    overall_comment: str


class FeedbackRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    meta: Meta | None = None


class FeedbackResponse(BaseModel):
    language_feedback: LanguageFeedback
    meta: dict | None = None

# Class for achivmetns and stats


class ErrorIn(BaseModel):
    type: str
    subtype: str | None = None
    original: str | None = None
    corrected: str | None = None


class MessageIn(BaseModel):
    id: int
    text_original: str
    text_corrected: str | None = None
    explanation: str | None = None
    answer: str | None = None
    created_at: datetime | None = None


class MessageProcessedIn(BaseModel):
    tg_id: int
    username: str | None = None
    message: MessageIn
    errors: list[ErrorIn] = Field(default_factory=list)


class AchievementOut(BaseModel):
    code: int
    title: str
    description: str


class MessageProcessedOut(BaseModel):
    ok: bool
    user_id: int
    saved_message_id: int
    streak_days: int
    new_achievements: list[AchievementOut]
