# src/app.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.settings import get_settings
from src.schemas import ReplyRequest, ReplyResponse, FeedbackRequest, FeedbackResponse
from src.model import AIWorkerModel
from src.service import AIWorkerService


def create_app() -> FastAPI:
    app = FastAPI(title="AI Worker", version="1.0.0")

    @app.on_event("startup")
    def startup() -> None:
        settings = get_settings()

        model = AIWorkerModel(settings)
        model.model.eval()

        service = AIWorkerService(model=model, settings=settings)

        app.state.settings = settings
        app.state.service = service
        app.state.model_id = settings.MODEL_ID

    @app.get("/health")
    def health():
        # if startup failed, app won't be running anyway, but we keep this explicit
        model_id = getattr(app.state, "model_id", None)
        return {"status": "ok", "model_id": model_id}

    @app.post("/api/v1/worker/reply", response_model=ReplyResponse)
    def worker_reply(req: ReplyRequest):
        service: AIWorkerService = app.state.service
        return service.make_reply(req)

    @app.post("/api/v1/worker/feedback", response_model=FeedbackResponse)
    def worker_feedback(req: FeedbackRequest):
        service: AIWorkerService = app.state.service
        return service.make_feedback(req)

    return app


app = create_app()
