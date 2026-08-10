from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.health import router as health_router
from app.api.v1.activity_logs import router as activity_log_router
from app.api.v1.agents import router as agents_router
from app.api.v1.console import router as console_router
from app.api.v1.infrastructure import router as infrastructure_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.maintenance import router as maintenance_router
from app.api.v1.memory_gateway import router as memory_gateway_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.model_router import router as model_router_router
from app.api.v1.tool_gateway import router as tool_gateway_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.intake import router as intake_router
from app.api.v1.auth import router as auth_router
from app.config.settings import settings
from app.infrastructure.auth_middleware import AuthMiddleware
from app.infrastructure.exceptions import (
    generic_exception_handler,
    validation_exception_handler,
)
from app.infrastructure.logging import setup_logging
from app.infrastructure.middleware import RequestContextMiddleware
from app.infrastructure.ratelimit_middleware import RateLimitMiddleware
from app.services.auth import get_current_user
from fastapi.staticfiles import StaticFiles

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
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(activity_log_router)
app.include_router(model_router_router)
app.include_router(tool_gateway_router)
app.include_router(memory_gateway_router)
app.include_router(knowledge_router)
app.include_router(maintenance_router)
app.include_router(agents_router)
app.include_router(workflows_router)
app.include_router(intake_router)
app.include_router(auth_router)
app.include_router(metrics_router)
app.include_router(console_router)
app.include_router(infrastructure_router)

# Root Route
@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return FileResponse("frontend/index.html")
    return {"message": "Shipyard Platform Operational", "env": settings.app_env}


# Protected Test Route
@app.get("/api/v1/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}


# Mount static frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
