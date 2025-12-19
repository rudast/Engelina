from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Literal

import aiohttp
import requests
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from pydantic import BaseModel
from pydantic import Field

app = FastAPI(title='Backend API', version='0.3.0')

AI_WORKER_URL = os.getenv(
    'AI_WORKER_URL', 'http://ai_worker_service:8001',
).rstrip('/')

_pending_codes: dict[str, dict[str, Any]] = {}
_user_tokens: dict[str, str] = {}
_user_levels: dict[str, str] = {}

CODE_TTL_MIN = int(os.getenv('CODE_TTL_MIN', '10'))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _make_code_5() -> str:
    return f"{random.randint(0, 99999):05d}"



@app.get('/api/health')
def health():
    return {'status': 'ok'}


# -------------------------
# классы: чекер
# -------------------------
class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1)
    level: str = Field(..., pattern=r'^(A1|A2|B1|B2|C1)$')


class ErrorItem(BaseModel):
    type: str
    subtype: str | None = None
    original: str
    corrected: str


class CheckResponse(BaseModel):
    corrected_text: str
    explanation: str
    errors: list[ErrorItem]


# -------------------------
# регистрация
# -------------------------
class AuthRequestCodeIn(BaseModel):
    tg_username: str = Field(..., min_length=3, max_length=64)


class AuthRequestCodeOut(BaseModel):
    status: str


class AuthVerifyIn(BaseModel):
    tg_username: str
    code: str = Field(..., min_length=5, max_length=5)


class AuthVerifyOut(BaseModel):
    token: str
    tg_username: str


# -------------------------
# настройки
# -------------------------
class SettingsIn(BaseModel):
    level: str = Field(..., pattern=r'^(A1|A2|B1|B2|C1|C2)$')


class SettingsOut(BaseModel):
    tg_username: str
    level: str


# -------------------------
# статистика
# -------------------------
class StatsTimePoint(BaseModel):
    date: str
    errors: int
    messages: int


class StatsErrorsByTypePoint(BaseModel):
    type: str
    count: int


class StatsAchievementItem(BaseModel):
    code: str
    title: str
    earned_at: str


class StatsResponse(BaseModel):
    period: Literal['day', 'week', 'all']
    messages_count: int
    errors_count: int
    errors_per_message: float
    errors_timeseries: list[StatsTimePoint]
    errors_by_type: list[StatsErrorsByTypePoint]
    achievements: list[StatsAchievementItem]


# -------------------------
# авторизация доп
# -------------------------
def _auth_username_from_header(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401, detail='Missing Authorization header',
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(
            status_code=401, detail='Invalid Authorization header format',
        )

    token = parts[1]
    username = _user_tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail='Invalid or expired token')
    return username


# -------------------------
# эндпоинты: чекер
# -------------------------
@app.post('/api/check', response_model=CheckResponse)
async def check(
    req: CheckRequest, authorization: str | None =
    Header(default=None),
):
    username = _auth_username_from_header(authorization)

    data = await get_response(f'http://backend:8000/api/v1/users/{username}')

    payload = {'tg_id': data['tg_id'], 'text_original': req.text}

    try:
        data = await post_response(
            'http://backend:8000/api/v1/messages',
            data=payload,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail='AI worker is unavailable')

    errors_parsed: list[ErrorItem] = []
    for e in data.get('errors', []):
        try:
            errors_parsed.append(ErrorItem(**e))
        except Exception:
            continue

    return CheckResponse(
        corrected_text=data.get('corrected_text', req.text),
        explanation=data.get('explanation', ''),
        errors=errors_parsed,
    )


# -------------------------
# авторизация
# -------------------------
@app.post('/api/auth/request-code', response_model=AuthRequestCodeOut)
async def request_code(payload: AuthRequestCodeIn):
    username = payload.tg_username.strip().lstrip('@')
    if not username:
        raise HTTPException(status_code=400, detail='tg_username is empty')

    code = _make_code_5()
    expires_at = _now_utc() + timedelta(minutes=CODE_TTL_MIN)
    _pending_codes[username] = {'code': code, 'expires_at': expires_at}

    data = await post_response(
        'http://backend:8000/api/v1/auth/verify',
        {
            'username': username,
            'code': code,
        },
    )
    if data is None:
        logging.getLogger(__name__).info('User not found.')
        raise HTTPException(status_code=404)

    return {'status': 'sent'}


@app.post('/api/auth/verify', response_model=AuthVerifyOut)
def verify_code(payload: AuthVerifyIn):
    username = payload.tg_username.strip().lstrip('@')
    rec = _pending_codes.get(username)
    if not rec:
        raise HTTPException(
            status_code=401, detail='No pending code for this user',
        )

    if _now_utc() > rec['expires_at']:
        _pending_codes.pop(username, None)
        raise HTTPException(status_code=401, detail='Code expired')

    if payload.code != rec['code']:
        raise HTTPException(status_code=401, detail='Invalid code')

    token = f"mock-{username}-{random.randint(100000, 999999)}"
    _user_tokens[token] = username
    _pending_codes.pop(username, None)

    return {'token': token, 'tg_username': username}


# -------------------------
# Эндпоинты: статистика
# -------------------------
@app.get('/api/settings', response_model=SettingsOut)
async def get_settings(authorization: str | None = Header(default=None)):
    username = _auth_username_from_header(authorization)
    data = await get_response(f'http://backend:8000/api/v1/users/{username}')
    return {'tg_username': username, 'level': data['level']}


@app.post('/api/settings', response_model=SettingsOut)
async def set_settings(
    payload: SettingsIn,
    authorization: str | None = Header(default=None),
):
    username = _auth_username_from_header(authorization)
    _user_levels[username] = payload.level
    await patch_response(
        url=f'http://backend:8000/api/v1/users/{username}/level',
        data={
            'level': payload.level,
        },
    )

    return {'tg_username': username, 'level': payload.level}


# -------------------------
# Эндпоинты: статистика
# -------------------------
@app.get('/api/stats', response_model=StatsResponse)
async def stats(
    period: Literal['day', 'week', 'all'] = Query(default='week'),
    authorization: str | None = Header(default=None),
):
    username = _auth_username_from_header(authorization)

    try:
        r = await get_response(f"http://backend:8000/api/v1/stats/?\
                               tg_username={username}\
                               &period={period}")
    except requests.RequestException:
        raise HTTPException(status_code=502, detail='AI worker is unavailable')

    if r is None:
        raise HTTPException(
            status_code=502, detail='AI worker error',
        )
    return r


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


async def patch_response(url: str, data: dict) -> None | dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
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
