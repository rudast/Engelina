from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

app = FastAPI()

class CheckRequest(BaseModel):
    user_id: int
    text: str
    level: str

class ErrorItem(BaseModel):
    type: str
    subtype: Optional[str] = None
    original: str
    corrected: str

class CheckResponse(BaseModel):
    corrected_text: str
    explanation: str
    errors: List[ErrorItem]

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/check", response_model=CheckResponse)
def check(req: CheckRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    #тут будет вызов ai_worker_service и сохранение в БД
    return CheckResponse(
        corrected_text=req.text,
        explanation="Mock explanation (connect ai_worker later).",
        errors=[]
    )

@app.get("/api/stats")
def stats(user_id: int, period: str = "week") -> Dict[str, Any]:
    #тут подключить репозитории участника 1
    return {
        "messages_count": 0,
        "errors_count": 0,
        "errors_per_message": 0,
        "activity": [],
        "errors_by_type": [],
    }
