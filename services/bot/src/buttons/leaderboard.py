from __future__ import annotations

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


def leaderboard_kb(current_index: int):
    total_categories = 3
    next_index = (current_index + 1) % total_categories
    prev_index = (current_index - 1) % total_categories

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='◀️',
                    callback_data=f"lb:goto:{prev_index}",
                ),
                InlineKeyboardButton(
                    text='Exit',
                    callback_data='lb:exit',
                ),
                InlineKeyboardButton(
                    text='▶️',
                    callback_data=f"lb:goto:{next_index}",
                ),
            ],
        ],
    )
