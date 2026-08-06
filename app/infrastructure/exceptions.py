from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(
        "unhandled_exception", error=str(exc), request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning("validation_error", errors=exc.errors(), request_id=request_id)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": exc.errors(),
                "request_id": request_id,
            }
        },
    )
