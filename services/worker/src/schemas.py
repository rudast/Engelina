from typing import Literal, Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


#Class for feedback and reply

class ChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class Meta(BaseModel):
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] | None = "A2"
    platform: Literal["telegram", "web"]


class ReplyRequest(BaseModel):
    user_id: str
    session_id: str | None
    message: str
    history: List[ChatMessage] = []
    meta: Meta | None = None


class ReplyResponse(BaseModel):
    # user_id: str
    reply: str
    meta: dict | None = None


class FeedbackItem(BaseModel):
    user_text: str
    error_type: Literal['grammar', 'spelling', 'punctuation', 'style', 'vocabulary']
    explanation: str
    text_corrected: str | None


class LanguageFeedback(BaseModel):
    items: List[FeedbackItem]
    overall_comment: str

class FeedbackRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    meta: Meta | None = None

class FeedbackResponse(BaseModel):
    language_feedback: LanguageFeedback
    meta: dict | None = None

#Class for achivmetns and stats


class ErrorIn(BaseModel):
    type: str
    subtype: Optional[str] = None
    original: Optional[str] = None
    corrected: Optional[str] = None

class MessageIn(BaseModel):
    id: int
    text_original: str
    text_corrected: Optional[str] = None
    explanation: Optional[str] = None
    answer: Optional[str] = None
    created_at: Optional[datetime] = None

class MessageProcessedIn(BaseModel):
    tg_id: int
    username: Optional[str] = None
    message: MessageIn
    errors: List[ErrorIn] = Field(default_factory=list)

class AchievementOut(BaseModel):
    code: int
    title: str
    description: str

class MessageProcessedOut(BaseModel):
    ok: bool
    user_id: int
    saved_message_id: int
    streak_days: int
    new_achievements: List[AchievementOut]