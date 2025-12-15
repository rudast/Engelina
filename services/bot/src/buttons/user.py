from __future__ import annotations

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


btn_like = InlineKeyboardButton(
    text='👍🏻',
    callback_data='like_callback',
)

btn_dislike = InlineKeyboardButton(
    text='👎🏻',
    callback_data='dislike_callback',
)

rate_beyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_like, btn_dislike]])
