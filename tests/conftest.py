import pytest
from app.infrastructure.ratelimit_middleware import rate_limit_store

@pytest.fixture(autouse=True)
def clear_rate_limit_caches():
    rate_limit_store.clear()
