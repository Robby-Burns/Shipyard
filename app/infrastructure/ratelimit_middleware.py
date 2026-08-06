import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from cachetools import TTLCache
from app.config.settings import settings

# In‑process cache: keys → (tokens, last_refill_timestamp)
_cache = TTLCache(maxsize=10_000, ttl=60)
# Spend cap tracking: cumulative request tokens consumed per day (24h = 86400s)
_spend = TTLCache(maxsize=10_000, ttl=86400)

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
        # Token bucket state: (tokens, last_refill_timestamp)
        bucket = _cache_get(key)
        now = time.time()
        if bucket is None:
            tokens = limit
            last = now
        else:
            tokens, last = bucket
            # Refill based on elapsed time (seconds)
            elapsed = now - last
            refill = (elapsed / 60) * limit
            tokens = min(limit, tokens + refill)
            last = now
        if tokens < 1:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests – rate limit exceeded"},
            )
        # Consume a token
        tokens -= 1
        _cache_set(key, (tokens, last))
        # Spend‑cap tracking (cumulative tokens used)
        cap = getattr(settings, "spend_cap_per_user", None)
        if cap is not None:
            used = _spend_get(key)
            if used + 1 > cap:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Spend cap exceeded"},
                )
            _spend_inc(key)
        return await call_next(request)

def _cache_get(key: str):
    return _cache.get(key)

def _cache_set(key: str, value) -> None:
    _cache[key] = value

def _spend_get(key: str) -> int:
    return _spend.get(key, 0)

def _spend_inc(key: str) -> None:
    _spend[key] = _spend.get(key, 0) + 1
