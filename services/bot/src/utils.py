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
