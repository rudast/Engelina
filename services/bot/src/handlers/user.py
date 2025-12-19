from __future__ import annotations

import logging
from datetime import datetime

from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram.types import Message
from buttons.achievement import achievements_kb
from buttons.leaderboard import leaderboard_kb
from buttons.stats import link_keyboard
from buttons.user import rate_beyboard
from utils import format_daily_stats
from utils import format_leaderboard
from utils import get_response
from utils import post_response


router = Router()


@router.message(CommandStart())
async def start_cmd(msg: Message):
    res = await post_response(
        url='http://backend:8000/api/v1/users',
        data={
            'tg_id': msg.from_user.id,
            'username': msg.from_user.username,
        },
        msg=msg,
    )

    if res is None:
        return

    await msg.answer(
        '''
        ✨ Welcome to Engelina!

I'm your personal assistant — here to chat, help, and guide you anytime.
You can open your personal statistics on the website using the button below.

Use the menu buttons or simply send me any message to start the conversation. 😊
        ''',
    )


@router.message(Command(commands='help'))
async def help_cmd(msg: Message):
    await msg.delete()
    await msg.answer(
        '''
        ℹ️ Here’s what I can do:
    • Chat with you — just send any message
    • Show your personal statistics
    • Tell you more about the project
    • Guide you to the main website
    • View your achievements
    • Follow leaderboard

Commands:
    • /start — Restart the bot
    • /stats — Open your personal statistics
    • /about — About the project
    • /help — Show this help message
    • /achievements - Open your achievements
    • /leaderboard - Show leaderboard by groups
        ''',
    )


@router.message(Command(commands='stats'))
async def stats_cmd(msg: Message):
    await msg.delete()
    username = msg.from_user.username or f"user_{msg.from_user.id}"

    try:
        stats = await get_response(f"http://backend:8000/api/v1/stats/?\
                               tg_username={username}\
                               &period=day")

        if not stats:
            raise ValueError('No data received')

        text = format_daily_stats(stats)

    except Exception as e:
        logging.error(f"Stats fetch error: {str(e)}")
        text = (
            '⚠️ <b>Temporary issue loading stats</b>\n'
            'Your data will be available shortly.\n\n'
            '📊 Detailed statistics always available on the website:'
        )

    await msg.answer(
        text,
        reply_markup=link_keyboard,
        parse_mode='HTML',
    )


@router.message(Command(commands='about'))
async def about_cmd(msg: Message):
    await msg.delete()
    await msg.answer(
        '''
        💡 About Engelina

Engelina is an assistant created to help you track your progress, \
    view statistics, and have simple, friendly conversations.

I'm always here to help — just send a message!
        ''',
    )


@router.message(F.text & ~F.text.startswith('/'))
async def message(msg: Message):
    res = await post_response(
        url='http://backend:8000/api/v1/messages',
        data={
            'tg_id': msg.from_user.id,
            'text_original': msg.text,
        },
        msg=msg,
    )

    if res is None:
        return

    text_parts = []

    if res['answer']:
        text_parts.append(f"<b>Answer:</b>\n{res['answer']}")

    if res['text_corrected']:
        text_parts.append(
            f"<b>Corrected:</b>\n<code>{res['text_corrected']}</code>",
        )

    if res['explanation']:
        text_parts.append(f"<b>Explanation:</b>\n{res['explanation']}")

    text = '\n\n'.join(text_parts)

    await msg.reply(text, reply_markup=rate_beyboard)


@router.message(Command('achievements'))
async def cmd_achievements(msg: Message):
    tg_id = msg.from_user.id
    index = 0
    data = await get_response(f'http://backend:8000/api/v1/achievements/{
        tg_id
    }?index={index}')

    logging.getLogger(__name__).info(type(data))
    if data is None:
        await msg.answer('You have no achievements 😢')
        return

    earned_at = datetime.fromisoformat(data['earned_at'])
    formatted_date = earned_at.strftime('%d %b %Y, %H:%M')

    text = (f"🏆 <b>{data['title']}</b>\n\n"
            f"{data['description']}\n\n"
            f"📅 Received: {formatted_date}\n"
            f"({data['index']+1}/{data['total']})")

    await msg.delete()
    await msg.answer(text, reply_markup=achievements_kb(data['index']))


@router.callback_query(F.data == 'like_callback')
async def process_like_btn(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.answer()


@router.callback_query(F.data == 'dislike_callback')
async def process_dislike_btn(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith('ach:'))
async def ach_callback(query: CallbackQuery):
    data = query.data
    parts = data.split(':')
    action = parts[1]

    if action == 'exit':
        try:
            await query.message.delete()
        except Exception:
            await query.message.edit_reply_markup(None)
        await query.answer()
        return

    if action == 'goto':
        new_index = int(parts[2])
        tg_id = query.from_user.id
        data = await get_response(f'http://backend:8000/api/v1/achievements/{
            tg_id
        }?index={new_index}')

        earned_at = datetime.fromisoformat(data['earned_at'])
        formatted_date = earned_at.strftime('%d %b %Y, %H:%M')

        text = (f"🏆 <b>{data['title']}</b>\n\n"
                f"{data['description']}\n\n"
                f"📅 Received: {formatted_date}\n"
                f"({data['index']+1}/{data['total']})")

        try:
            await query.message.edit_text(
                text, reply_markup=achievements_kb(data['index']),
            )
        except TelegramBadRequest:
            pass

        await query.answer()


@router.message(Command(commands='leaderboard'))
async def leaderboard_cmd(msg: Message):
    category_index = 0
    data = await get_response(
        f'http://backend:8000/api/v1/leaderboard/{category_index}',
    )

    if data is None:
        await msg.delete()
        await msg.answer('🏆 Leaderboard temporarily unavailable. \
                         Try again later.')
        return

    text = format_leaderboard(data)
    await msg.delete()
    await msg.answer(text, reply_markup=leaderboard_kb(category_index))


@router.callback_query(lambda c: c.data.startswith('lb:'))
async def leaderboard_callback(query: CallbackQuery):
    parts = query.data.split(':')
    action = parts[1]

    if action == 'exit':
        try:
            await query.message.delete()
        except Exception:
            await query.message.edit_reply_markup(None)
        await query.answer()
        return

    if action == 'goto':
        new_index = int(parts[2])
        data = await get_response(
            f'http://backend:8000/api/v1/leaderboard/{new_index}',
        )

        if data is None:
            await query.answer('⚠️ Data unavailable', show_alert=True)
            return

        text = format_leaderboard(data)
        try:
            await query.message.edit_text(
                text,
                reply_markup=leaderboard_kb(new_index),
                parse_mode='HTML',
            )
        except TelegramBadRequest:
            await query.answer()
        return
