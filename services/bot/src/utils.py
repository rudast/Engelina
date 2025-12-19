from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import aiohttp
from aiogram.types import Message


async def post_response(url: str, data: dict, msg: Message) -> None | dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=data,
                timeout=100,
            ) as resp:

                if resp.status < 200 or resp.status >= 300:
                    await send_error_msg(msg)
                    logging.getLogger(__name__).error(
                        f'Responce error. Status: {resp.status}',
                    )
                    return None

                data = await resp.json()
                return dict(data)

    except aiohttp.ClientError:
        await send_error_msg(msg)
        logging.getLogger(__name__).error('Server error.')
    except asyncio.TimeoutError:
        await send_error_msg(msg)
        logging.getLogger(__name__).error('Timeout error.')
    except Exception:
        await send_error_msg(msg)
        logging.getLogger(__name__).error('Unknow error.')

    return None


async def send_error_msg(msg: Message) -> None:
    await msg.answer(
        '''
        ⚠️ Oops! Engelina is currently unavailable.
Please try again later.''',
    )
    return None


async def get_response(url: str) -> None | dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=100,
            ) as resp:

                if resp.status < 200 or resp.status >= 300:
                    logging.getLogger(__name__).error(
                        f'Responce error. Status: {resp.status}',
                    )
                    return None

                data = await resp.json()
                return dict(data)

    except aiohttp.ClientError:
        logging.getLogger(__name__).error('Server error.')
    except asyncio.TimeoutError:
        logging.getLogger(__name__).error('Timeout error.')
    except Exception:
        logging.getLogger(__name__).error('Unknow error.')

    return None


def format_leaderboard(data: dict) -> str:
    category_titles = {
        0: '📩 <b>Top by Messages</b>',
        1: '❌ <b>Top by Errors</b>',
        2: '🏅 <b>Top by Achievements</b>',
    }

    header = category_titles.get(data['current_index'], '🏆 <b>Leaderboard</b>')
    entries = []

    for i, entry in enumerate(data['entries'], 1):
        username = entry['username'] or f"user_{entry['user_id']}"
        medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '•'
        entries.append(f"{medal} @{username} - <b>{entry['value']}</b>")

    footer = f"\n\n(<i>{data['current_index']+1}/{
        data['total_categories']
    }</i>)"
    return f"{header}\n\n" + '\n'.join(entries) + footer


def format_daily_stats(stats: dict) -> str:
    today = datetime.utcnow().strftime('%d %b %Y')

    achievements_count = len(stats.get('achievements', []))

    level_info = ''
    if stats.get('level_progress'):
        progress = stats['level_progress']
        level_info = (
            f"\n\n📈 <b>Level Progress</b>\n"
            f"{progress['current_level']} → {progress['next_level']} "
            f"({progress['percent']}% completed)"
        )

    return (
        f"📊 <b>Personal Statistics</b> (Today: {today})\n\n"
        f"💬 <b>Messages:</b> {stats['messages_count']}\n"
        f"❌ <b>Errors corrected:</b> {stats['errors_count']}\n"
        f"📉 <b>Errors per message:</b> {stats['errors_per_message']}\n"
        f"🏆 <b>Achievements earned:</b> {achievements_count}{level_info}\n\n"
        f"🌐 Tap button below to see full statistics with charts and details:"
    )
