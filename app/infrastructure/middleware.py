import time
import uuid
from fastapi import Request
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Bind context variables for structured logs in this request execution context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            logger.info(
                "request_processed",
                status_code=response.status_code,
                duration_seconds=round(process_time, 4),
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"
            return response
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                error=str(exc),
                duration_seconds=round(process_time, 4),
            )
            raise exc
