from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.config.settings import settings
from app.infrastructure.exceptions import (
    generic_exception_handler,
    validation_exception_handler,
)
from app.infrastructure.logging import setup_logging
from app.infrastructure.middleware import RequestContextMiddleware
from app.services.auth import get_current_user

# Initialize logging configuration
setup_logging()

app = FastAPI(title="Shipyard API", version="0.1.0", debug=settings.debug)

# Exception Handlers
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(
    RequestValidationError, validation_exception_handler
)

# Middleware
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)


@app.get("/")
async def root():
    return {"message": "Shipyard Platform Operational", "env": settings.app_env}


# Protected Test Route
@app.get("/api/v1/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}
