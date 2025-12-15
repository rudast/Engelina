from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import Message
from settings import get_bot_settings


class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.from_user is None:
            return

        if event.from_user.id not in get_bot_settings().ADMINS:
            return

        return await handler(event, data)
