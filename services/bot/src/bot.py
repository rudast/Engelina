from __future__ import annotations

import logging
import sys

from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from settings import get_bot_settings


async def setup_bot() -> Bot:
    bot = Bot(
        token=get_bot_settings().TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        await bot.get_me()
        logging.getLogger(__name__).info('Bot successfully authorized')
    except TelegramUnauthorizedError:
        logging.getLogger(__name__).critical('Incorrect token')
        await bot.session.close()
        sys.exit(1)

    return bot
