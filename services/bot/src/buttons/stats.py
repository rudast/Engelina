from __future__ import annotations

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


link = InlineKeyboardButton(
    text='🌐 Open Full Statistics',
    url='https://t.me/engelinabot',
)


link_keyboard = InlineKeyboardMarkup(inline_keyboard=[[link]])
