from __future__ import annotations

import asyncio
import enum
import logging

import aiohttp
from src.settings import get_bot_settings


class ErrorTypeEnum(enum.Enum):
    spelling = 'Spelling'
    grammar = 'Grammar'
    punctuation = 'Punctuation'
    style = 'Style'


class LevelTypeEnum(enum.Enum):
    a1 = 'A1'
    a2 = 'A2'
    b1 = 'B1'
    b2 = 'B2'
    c1 = 'C1'
    c2 = 'C2'


async def send_notice(tg_id: int, text: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f'https://api.telegram.org/bot{
                    get_bot_settings().TOKEN
                }/sendMessage',
                timeout=5,
                data={
                    'chat_id': tg_id,
                    'text': text,
                },
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


async def post_response(url: str, data: dict) -> None | dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=data,
                timeout=200,
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


async def get_response(url: str) -> None | dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=200,
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
