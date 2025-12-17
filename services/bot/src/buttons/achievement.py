from __future__ import annotations

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def achievements_kb(index: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='◀️', callback_data=f"ach:goto:{index-1}",
                ),
                InlineKeyboardButton(text='Exit', callback_data='ach:exit'),
                InlineKeyboardButton(
                    text='▶️', callback_data=f"ach:goto:{index+1}",
                ),
            ],
        ],
    )
