import os
import random
import requests

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, List, Literal

from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Backend API", version="0.3.0")

AI_WORKER_URL = os.getenv("AI_WORKER_URL", "http://ai_worker_service:8001").rstrip("/")

_pending_codes: Dict[str, Dict[str, Any]] = {}  # username -> {code, expires_at}
_user_tokens: Dict[str, str] = {}  # token -> username
_user_levels: Dict[str, str] = {}  # username -> level

CODE_TTL_MIN = int(os.getenv("CODE_TTL_MIN", "10"))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _make_code_5() -> str:
    return f"{random.randint(0, 99999):05d}"


def _send_code_to_telegram_mock(username: str, code: str) -> None:
    print(f"[AUTH MOCK] Send code to @{username}: {code}")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# -------------------------
# MODELS: CHECK
# -------------------------
class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1)
    level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1)$")


class ErrorItem(BaseModel):
    type: str
    subtype: Optional[str] = None
    original: str
    corrected: str


class CheckResponse(BaseModel):
    corrected_text: str
    explanation: str
    errors: List[ErrorItem]


# -------------------------
# MODELS: AUTH
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
# MODELS: SETTINGS
# -------------------------
class SettingsIn(BaseModel):
    level: str = Field(..., pattern=r"^(A1|A2|B1|B2|C1)$")


class SettingsOut(BaseModel):
    tg_username: str
    level: str


# -------------------------
# MODELS: STATS (новый контракт)
# -------------------------
class StatsTimePoint(BaseModel):
    date: str      # YYYY-MM-DD
    errors: int
    messages: int


class StatsErrorsByTypePoint(BaseModel):
    type: str
    count: int


class StatsAchievementItem(BaseModel):
    code: str
    title: str
    earned_at: str  # YYYY-MM-DD


class StatsResponse(BaseModel):
    period: Literal["day", "week", "all"]
    messages_count: int
    errors_count: int
    errors_per_message: float
    errors_timeseries: List[StatsTimePoint]
    errors_by_type: List[StatsErrorsByTypePoint]
    achievements: List[StatsAchievementItem]


# -------------------------
# AUTH HELPERS
# -------------------------
def _auth_username_from_header(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]
    username = _user_tokens.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


# -------------------------
# ENDPOINTS: CHECK (через ai_worker_stub)
# -------------------------
@app.post("/api/check", response_model=CheckResponse)
def check(req: CheckRequest, authorization: Optional[str] = Header(default=None)):
    username = _auth_username_from_header(authorization)

    # если user сохранил level в Settings — используем его
    level = _user_levels.get(username, req.level)

    payload = {"tg_username": username, "text": req.text, "level": level}

    try:
        r = requests.post(f"{AI_WORKER_URL}/internal/analyze", json=payload, timeout=60)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="AI worker is unavailable")

    if not r.ok:
        raise HTTPException(status_code=502, detail=f"AI worker error: {r.status_code}")

    try:
        data = r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="AI worker returned invalid JSON")

    # мягкий парсинг errors, чтобы не падать из-за одного плохого элемента
    errors_parsed: List[ErrorItem] = []
    for e in data.get("errors", []):
        try:
            errors_parsed.append(ErrorItem(**e))
        except Exception:
            continue

    return CheckResponse(
        corrected_text=data.get("corrected_text", req.text),
        explanation=data.get("explanation", ""),
        errors=errors_parsed,
    )


# -------------------------
# ENDPOINTS: AUTH
# -------------------------
@app.post("/api/auth/request-code", response_model=AuthRequestCodeOut)
def request_code(payload: AuthRequestCodeIn):
    username = payload.tg_username.strip().lstrip("@")
    if not username:
        raise HTTPException(status_code=400, detail="tg_username is empty")

    code = _make_code_5()
    expires_at = _now_utc() + timedelta(minutes=CODE_TTL_MIN)
    _pending_codes[username] = {"code": code, "expires_at": expires_at}

    _send_code_to_telegram_mock(username, code)
    return {"status": "sent"}


@app.post("/api/auth/verify", response_model=AuthVerifyOut)
def verify_code(payload: AuthVerifyIn):
    username = payload.tg_username.strip().lstrip("@")
    rec = _pending_codes.get(username)
    if not rec:
        raise HTTPException(status_code=401, detail="No pending code for this user")

    if _now_utc() > rec["expires_at"]:
        _pending_codes.pop(username, None)
        raise HTTPException(status_code=401, detail="Code expired")

    if payload.code != rec["code"]:
        raise HTTPException(status_code=401, detail="Invalid code")

    token = f"mock-{username}-{random.randint(100000, 999999)}"
    _user_tokens[token] = username
    _pending_codes.pop(username, None)

    return {"token": token, "tg_username": username}


# -------------------------
# ENDPOINTS: SETTINGS
# -------------------------
@app.get("/api/settings", response_model=SettingsOut)
def get_settings(authorization: Optional[str] = Header(default=None)):
    username = _auth_username_from_header(authorization)
    level = _user_levels.get(username, "B1")
    return {"tg_username": username, "level": level}


@app.post("/api/settings", response_model=SettingsOut)
def set_settings(payload: SettingsIn, authorization: Optional[str] = Header(default=None)):
    username = _auth_username_from_header(authorization)
    _user_levels[username] = payload.level
    return {"tg_username": username, "level": payload.level}


# -------------------------
# ENDPOINTS: STATS (через ai_worker_stub)
# -------------------------
@app.get("/api/stats", response_model=StatsResponse)
def stats(
    period: Literal["day", "week", "all"] = Query(default="week"),
    authorization: Optional[str] = Header(default=None),
):
    username = _auth_username_from_header(authorization)

    try:
        r = requests.get(
            f"{AI_WORKER_URL}/internal/stats",
            params={"tg_username": username, "period": period},
            timeout=20,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="AI worker is unavailable")

    if not r.ok:
        raise HTTPException(status_code=502, detail=f"AI worker error: {r.status_code}")

    try:
        data = r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="AI worker returned invalid JSON")

    return data
