from __future__ import annotations

import asyncio
import logging

import aiohttp
from aiogram.types import Message


async def post_response(url: str, data: dict, msg: Message) -> None | dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=data,
                timeout=5,
            ) as resp:

                if resp.status != 200:
                    await send_error_msg(msg)
                    logging.getLogger(__name__).error(
                        f'Responce error. Status: {resp.status}',
                    )
                    return None

                data = await resp.json()
                return dict(data)

    except aiohttp.ClientError:
        await send_error_msg(msg)
        logging.getLogger(__name__).error(f'Server error.')
    except asyncio.TimeoutError:
        await send_error_msg(msg)
        logging.getLogger(__name__).error(f'Timeout error.')
    except Exception:
        await send_error_msg(msg)
        logging.getLogger(__name__).error(f'Unknow error.')


async def send_error_msg(msg: Message) -> None:
    await msg.answer(
        '''
        ⚠️ Oops! Engelina is currently unavailable.
        Please try again later.''',
    )
