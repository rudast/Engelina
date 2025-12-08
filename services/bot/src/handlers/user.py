from __future__ import annotations

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.types import Message


router = Router()


@router.message(CommandStart())
async def start_cmd(msg: Message):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://backend:8000/users/start',
            json={'tg_id': msg.from_user.id},
        ) as resp:
            data = await resp.json()

    await msg.answer(str(data))


@router.message(Command(commands='help'))
async def help_cmd(msg: Message):
    pass
