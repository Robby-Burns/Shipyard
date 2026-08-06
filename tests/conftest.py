import pytest
from app.infrastructure.ratelimit_middleware import _cache, _spend

@pytest.fixture(autouse=True)
def clear_rate_limit_caches():
    _cache.clear()
    _spend.clear()
