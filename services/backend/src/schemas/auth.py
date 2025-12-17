from __future__ import annotations

from pydantic import BaseModel


class AuthRequest(BaseModel):
    username: str
    code: str
