import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from cachetools import TTLCache
from app.config.settings import settings

# In‑process cache: keys → (request count, expiry handled by TTLCache)
# TTL is one minute (60 seconds) matching the rate‑limit window.
_cache = TTLCache(maxsize=10_000, ttl=60)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces a simple per‑user/IP request rate limit.

    The key is derived from the authenticated ``sub`` claim when a valid JWT
    payload is present on ``request.state.user`` (populated by ``AuthMiddleware``).
    If no user is authenticated, the client IP address is used.
    Admin routes (paths under ``/admin``) are excluded.
    """

    async def dispatch(self, request: Request, call_next):
        # Bypass admin or internal routes.
        if request.url.path.startswith("/admin"):
            return await call_next(request)

        # Determine bucket key.
        user_payload = getattr(request.state, "user", None)
        if isinstance(user_payload, dict) and "sub" in user_payload:
            key = f"user:{user_payload['sub']}"
        else:
            # client.host may be None in tests; fallback to IP string.
            key = f"ip:{request.client.host if request.client else 'unknown'}"

        limit = getattr(settings, "rate_limit_requests_per_minute", 60)
        count = _cache_get(key)
        if count >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests – rate limit exceeded"},
            )
        _cache_inc(key)
        return await call_next(request)

def _cache_get(key: str) -> int:
    """Return current request count for *key* (0 if not present)."""
    return _cache.get(key, 0)

def _cache_inc(key: str) -> None:
    """Increment request count for *key*.
    ``TTLCache`` automatically resets the entry after its TTL.
    """
    _cache[key] = _cache.get(key, 0) + 1
