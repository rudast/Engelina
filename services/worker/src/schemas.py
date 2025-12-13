from typing import Literal, List

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal['user', 'assistent']
    content: str


class Meta(BaseModel):
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2"] | None
    platform: Literal["telegram", "web"]


class ReplyRequest(BaseModel):
    user_id: str
    session_id: str | None
    message: str
    hystory: List[ChatMessage] = []
    meta: Meta | None = None


class ReplyResponse(BaseModel):
    user_id: str
    reply: str
    meta: dict | None = None


class FeedbackItem(BaseModel):
    user_text: str
    error_type: Literal['grammar', 'vocabulary', 'word_order', 'spelling', 'punctuation', 'style', 'other']
    explanation: str
    suggested_corrected: str | None


class LanguageFeedback:
    items: List[FeedbackItem]
    overall_coment: str

class FeedbackRequest(BaseModel):
    user_id: str
    session_id: str
    message: str
    meta: Meta | None = None

