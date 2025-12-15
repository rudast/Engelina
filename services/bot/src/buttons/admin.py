from __future__ import annotations

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


btn_confirm = InlineKeyboardButton(
    text='✅',
    callback_data='confirm_callback',
)

btn_cancel = InlineKeyboardButton(
    text='❌',
    callback_data='cancel_callback',
)

admin_answer_btns = InlineKeyboardMarkup(
    inline_keyboard=[[btn_confirm, btn_cancel]],
)
