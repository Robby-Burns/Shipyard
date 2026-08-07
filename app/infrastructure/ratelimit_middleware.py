import time
import asyncio
from typing import Optional, Tuple
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from cachetools import TTLCache
from app.config.settings import settings


class RateLimitStore:
    """Abstract rate limiter store.

    Can be subclassed in the future to implement distributed locking and storage
    (e.g., RedisRateLimitStore) without modifying the middleware layout.
    """

    async def check_and_consume(
        self, key: str, limit: int, cap: Optional[int]
    ) -> Tuple[bool, str]:
        raise NotImplementedError()


class InMemoryRateLimitStore(RateLimitStore):
    """Process-local thread-safe rate limit store.

    Uses cachetools.TTLCache and asyncio.Lock to execute token-bucket and spend-cap
    operations atomically. Note: Rate limiting is scoped to the current process event loop.
    """

    def __init__(self):
        # Keys -> (tokens, last_refill_timestamp)
        self._cache = TTLCache(maxsize=10_000, ttl=60)
        # Daily spend cap tracking: cumulative request tokens consumed (24h TTL)
        self._spend = TTLCache(maxsize=10_000, ttl=86400)
        self._key_locks = TTLCache(maxsize=10_000, ttl=300)  # per-key asyncio.Lock with TTL

    # Helper to get lock for a specific key
    async def _get_lock(self, key: str) -> asyncio.Lock:
        lock = self._key_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._key_locks[key] = lock
        return lock

    async def check_and_consume(
        self, key: str, limit: int, cap: Optional[int]
    ) -> Tuple[bool, str]:
        # Acquire per-key lock for atomic check/consume
        lock = await self._get_lock(key)
        async with lock:
            now = time.time()

            # 1. Rate Limiting Check (Token Bucket)
            bucket = self._cache.get(key)
            if bucket is None:
                tokens = float(limit)
                last_refill = now
            else:
                tokens, last_refill = bucket
                elapsed = now - last_refill
                # Refill rate: limit requests per 60 seconds
                refill = (elapsed / 60.0) * limit
                tokens = min(float(limit), tokens + refill)
                last_refill = now

            if tokens < 1.0:
                return False, "Too Many Requests – rate limit exceeded"

            # 2. Spend Cap Check (Cumulative Daily Request Cap)
            if cap is not None:
                used = self._spend.get(key, 0)
                if used + 1 > cap:
                    return False, "Spend cap exceeded"

            # 3. Consume token & increment spend count
            tokens -= 1.0
            self._cache[key] = (tokens, last_refill)
            if cap is not None:
                self._spend[key] = self._spend.get(key, 0) + 1

            return True, ""

    def clear(self):
        """Reset caches for testing and isolation."""
        self._cache.clear()
        self._spend.clear()


# Process-local stateful store. Replace with a distributed store when scaling horizontally.
rate_limit_store = InMemoryRateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces a pluggable rate limit and per-user spend-cap.

    Extracts user identity from `request.state.user` (JWT sub claim) if authenticated,
    otherwise falls back to client IP address. Excludes routes matching `/admin`.
    """

    async def dispatch(self, request: Request, call_next):
        # Bypass admin or internal routes only for exact /admin path or its subpaths, not for similarly prefixed paths
        path = request.url.path
        # Exact match or subpath under /admin/
        if path == "/admin" or path.startswith("/admin/"):
            return await call_next(request)

        # Derive rate-limiting key
        user_payload = getattr(request.state, "user", None)
        if isinstance(user_payload, dict) and "sub" in user_payload:
            key = f"user:{user_payload['sub']}"
        else:
            client_host = request.client.host if request.client else "unknown"
            key = f"ip:{client_host}"

        limit = getattr(settings, "rate_limit_requests_per_minute", 60)
        cap = getattr(settings, "spend_cap_per_user", None)

        allowed, message = await rate_limit_store.check_and_consume(
            key, limit, cap
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": message},
            )

        return await call_next(request)
