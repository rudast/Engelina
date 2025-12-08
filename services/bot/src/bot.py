from __future__ import annotations

import logging
import sys

from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError
from settings import BotSettings


async def setup_bot(logger: logging.Logger, settings: BotSettings) -> Bot:
    bot = Bot(
        token=settings.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        await bot.get_me()
        logger.info('Bot successfully authorized')
    except TelegramUnauthorizedError:
        logger.critical('Incorrect token')
        await bot.session.close()
        sys.exit(1)

    return bot
