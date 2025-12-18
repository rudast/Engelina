from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date, timedelta
import hashlib

app = FastAPI(title="AI Worker Stub", version="0.1.0")


class AnalyzeIn(BaseModel):
    tg_username: str
    text: str
    level: str


class ErrorItem(BaseModel):
    type: str
    subtype: Optional[str] = None
    original: str
    corrected: str


class AnalyzeOut(BaseModel):
    corrected_text: str
    explanation: str
    errors: List[ErrorItem]


class StatsTimePoint(BaseModel):
    date: str
    errors: int
    messages: int


class ErrorsByTypePoint(BaseModel):
    type: str
    count: int


class AchievementItem(BaseModel):
    code: str
    title: str
    earned_at: str


class StatsOut(BaseModel):
    period: Literal["day", "week", "all"]
    messages_count: int
    errors_count: int
    errors_per_message: float
    errors_timeseries: List[StatsTimePoint]
    errors_by_type: List[ErrorsByTypePoint]
    achievements: List[AchievementItem]


@app.get("/internal/health")
def health():
    return {"status": "ok"}


@app.post("/internal/analyze", response_model=AnalyzeOut)
def analyze(payload: AnalyzeIn):
    # демо: возвращаем текст без исправлений, только структура
    return {
        "corrected_text": payload.text,
        "explanation": f"Stub AI: level={payload.level}, user=@{payload.tg_username}",
        "errors": [],
    }


def _seed_int(s: str) -> int:
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


@app.get("/internal/stats", response_model=StatsOut)
def stats(
    tg_username: str = Query(..., min_length=1),
    period: Literal["day", "week", "all"] = "week",
):
    username = tg_username.strip().lstrip("@")
    seed = _seed_int(f"{username}:{period}")
    today = date.today()

    days = 1 if period == "day" else 7 if period == "week" else 30  # all=30 дней для демо

    # errors_timeseries (для линейного графика)
    ts = []
    total_msgs = 0
    total_err = 0
    for i in range(days):
        d = today - timedelta(days=(days - 1 - i))
        msgs = (seed + i * 13) % 7          # 0..6
        errs = (seed + i * 17) % 11         # 0..10
        ts.append({"date": d.isoformat(), "errors": int(errs), "messages": int(msgs)})
        total_msgs += int(msgs)
        total_err += int(errs)

    errors_per_message = round((total_err / total_msgs), 2) if total_msgs > 0 else 0.0

    # errors_by_type (bar chart)
    types = ["grammar", "spelling", "vocabulary", "punctuation", "word_order"]
    ebt = []
    for j, t in enumerate(types):
        c = (seed // (j + 1) + j * 5) % 12
        ebt.append({"type": t, "count": int(c)})

    # achievements (списком)
    ach_pool = [
        ("FIRST_MESSAGE", "First message"),
        ("STREAK_3", "3-day streak"),
        ("STREAK_7", "7-day streak"),
        ("NO_ERRORS_5", "5 messages without errors"),
        ("100_MESSAGES_SENT", "100 messages sent"),
    ]
    achievements = []
    for k, (code, title) in enumerate(ach_pool):
        if ((seed + k * 7) % 2) == 0:
            earned = (today - timedelta(days=(seed + k) % max(days, 1))).isoformat()
            achievements.append({"code": code, "title": title, "earned_at": earned})

    return {
        "period": period,
        "messages_count": int(total_msgs),
        "errors_count": int(total_err),
        "errors_per_message": float(errors_per_message),
        "errors_timeseries": ts,
        "errors_by_type": ebt,
        "achievements": achievements,
    }
