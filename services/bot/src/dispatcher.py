from __future__ import annotations

from aiogram import Bot
from aiogram import Dispatcher
from handlers import admin
from handlers import user


async def setup_dispatcher(bot: Bot) -> Dispatcher:
    dp = Dispatcher()

    dp.include_routers(admin.router, user.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

    return dp
