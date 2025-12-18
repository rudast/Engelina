from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from src.logging_config import setup_logging
from src.queue import get_queue
from src.queue import get_redis
from src.schemas import FeedbackRequest
from src.schemas import ReplyRequest
from src.settings import get_settings
from src.utils import wait_job_result

logger = logging.getLogger('ai_worker.api')


def create_app() -> FastAPI:
    app = FastAPI(title='AI Worker API', version='1.0.0')

    @app.middleware('http')
    async def add_request_id(request: Request, call_next):
        rid = request.headers.get('x-request-id') or str(uuid.uuid4())
        request.state.request_id = rid

        logger.info(
            'http request: start | rid=%s method=%s path=%s client=%s',
            rid,
            request.method,
            request.url.path,
            getattr(request.client, 'host', None),
        )
        try:
            response = await call_next(request)
        except Exception:
            logger.exception('http request: unhandled error | rid=%s', rid)
            raise
        finally:
            logger.info(
                'http request: end | rid=%s method=%s path=%s',
                rid,
                request.method,
                request.url.path,
            )

        response.headers['x-request-id'] = rid
        return response

    @app.on_event('startup')
    def startup() -> None:
        settings = get_settings()
        setup_logging(settings.LOG_LEVEL)

        app.state.settings = settings
        app.state.redis = get_redis(settings)
        app.state.queue = get_queue(settings)

        logger.info(
            'startup: ok | redis_url=%s queue=%s '
            'result_ttl_s=%s job_timeout_s=%s',
            settings.REDIS_URL,
            settings.RQ_QUEUE_NAME,
            settings.RQ_RESULT_TTL_S,
            getattr(settings, 'JOB_TIMEOUT_S', 120),
        )

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.post('/api/v1/worker/reply')
    async def reply_wait(req: ReplyRequest, request: Request):
        settings = app.state.settings
        q = app.state.queue
        rid = request.state.request_id

        level = req.meta.level if req.meta else None
        hist = [{'role': m.role, 'content': m.content} for m in req.history]

        logger.info(
            'reply: enqueue | rid=%s user_id=%s '
            'session_id=%s level=%s hist_turns=%s',
            rid,
            req.user_id,
            req.session_id,
            level,
            len(hist),
        )

        job = q.enqueue(
            'src.tasks.task_reply',
            level=level,
            history=hist,
            message=req.message,
            result_ttl=settings.RQ_RESULT_TTL_S,
        )

        logger.info('reply: job created | rid=%s job_id=%s', rid, job.id)

        try:
            result = await wait_job_result(
                job,
                timeout_s=getattr(settings, 'JOB_TIMEOUT_S', 120),
            )
        except TimeoutError as e:
            logger.warning(
                'reply: timeout | rid=%s job_id=%s timeout_s=%s',
                rid,
                job.id,
                getattr(settings, 'JOB_TIMEOUT_S', 120),
            )
            raise HTTPException(status_code=504, detail=str(e))
        except Exception as e:
            logger.exception('reply: failed | rid=%s job_id=%s', rid, job.id)
            raise HTTPException(status_code=500, detail=f"job failed: {e}")

        logger.info('reply: done | rid=%s job_id=%s', rid, job.id)
        return {'request_id': rid, 'result': result}

    @app.post('/api/v1/worker/feedback')
    async def feedback_wait(req: FeedbackRequest, request: Request):
        settings = app.state.settings
        q = app.state.queue
        rid = request.state.request_id

        level = req.meta.level if req.meta else None

        logger.info(
            'feedback: enqueue | rid=%s user_id=%s session_id=%s level=%s',
            rid,
            req.user_id,
            req.session_id,
            level,
        )

        job = q.enqueue(
            'src.tasks.task_feedback',
            level=level,
            message=req.message,
            result_ttl=settings.RQ_RESULT_TTL_S,
        )

        logger.info('feedback: job created | rid=%s job_id=%s', rid, job.id)

        try:
            result = await wait_job_result(
                job,
                timeout_s=getattr(settings, 'JOB_TIMEOUT_S', 120),
            )
        except TimeoutError as e:
            logger.warning(
                'feedback: timeout | rid=%s job_id=%s timeout_s=%s',
                rid,
                job.id,
                getattr(settings, 'JOB_TIMEOUT_S', 120),
            )
            raise HTTPException(status_code=504, detail=str(e))
        except Exception as e:
            logger.exception(
                'feedback: failed | rid=%s job_id=%s', rid, job.id,
            )
            raise HTTPException(status_code=500, detail=f"job failed: {e}")

        logger.info('feedback: done | rid=%s job_id=%s', rid, job.id)
        return {'request_id': rid, 'result': result}

    return app


app = create_app()
