# src/app.py
from __future__ import annotations

import uuid
from fastapi import FastAPI, Request, HTTPException
from rq.job import Job
import asyncio

from src.utils import wait_job_result



from src.settings import get_settings
from src.queue import get_queue, get_redis
from src.schemas import ReplyRequest, FeedbackRequest
from src.logging_config import setup_logging


def create_app() -> FastAPI:
    app = FastAPI(title="AI Worker API", version="1.0.0")

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response

    @app.on_event("startup")
    def startup() -> None:
        settings = get_settings()
        app.state.settings = settings
        app.state.redis = get_redis(settings)
        app.state.queue = get_queue(settings)
        setup_logging()
        

    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    @app.post("/api/v1/worker/reply")
    async def reply_wait(req: ReplyRequest, request: Request):
        settings = app.state.settings
        q = app.state.queue

        level = req.meta.level if req.meta else None
        hist = [{"role": m.role, "content": m.content} for m in req.history]

        job = q.enqueue(
            "src.tasks.task_reply",
            level=level,
            history=hist,
            message=req.message,
            result_ttl=settings.RQ_RESULT_TTL_S,
        )


        try:
            result = await wait_job_result(job, timeout_s=getattr(settings, "JOB_TIMEOUT_S", 120))
        except TimeoutError as e:
            raise HTTPException(status_code=504, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"job failed: {e}")

        return {"request_id": request.state.request_id, "result": result}

    @app.post("/api/v1/worker/feedback")
    async def feedback_wait(req: FeedbackRequest, request: Request):
        settings = app.state.settings
        q = app.state.queue

        level = req.meta.level if req.meta else None

        job = q.enqueue(
            "src.tasks.task_feedback",
            level=level,
            message=req.message,
            result_ttl=settings.RQ_RESULT_TTL_S,
        )

        try:
            result = await wait_job_result(job, timeout_s=getattr(settings, "JOB_TIMEOUT_S", 120))
        except TimeoutError as e:
            raise HTTPException(status_code=504, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"job failed: {e}")

        return {"request_id": request.state.request_id, "result": result}

    # @app.get("/api/v1/worker/jobs/{job_id}")
    # def get_job(job_id: str):
    #     redis = app.state.redis
    #     try:
    #         job = Job.fetch(job_id, connection=redis)
    #     except Exception:
    #         raise HTTPException(status_code=404, detail="job not found")

    #     status = job.get_status()
    #     if status == "finished":
    #         return {"job_id": job.id, "status": status, "result": job.result}
    #     if status == "failed":
    #         return {"job_id": job.id, "status": status, "error": (job.exc_info or "")[-2000:]}
    #     return {"job_id": job.id, "status": status}

    return app


app = create_app()
