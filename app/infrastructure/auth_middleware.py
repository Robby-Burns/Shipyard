import jwt
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.settings import settings

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that validates the JWT (if present) and stores the payload
    on ``request.state.user``. It does **not** block the request – routes that
    require authentication will still use the ``get_current_user`` dependency
    which re‑validates the token. This middleware allows subsequent middlewares
    (e.g., rate‑limiting) to access the ``sub`` claim without having to decode
    the token again.
    """

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret_key,
                    algorithms=[settings.jwt_algorithm],
                )
                request.state.user = payload
            except jwt.PyJWTError:
                # Invalid token – we do not raise here; the dependency will
                # handle authentication failures for protected endpoints.
                request.state.user = None
        else:
            request.state.user = None
        return await call_next(request)
