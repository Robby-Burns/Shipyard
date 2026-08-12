import os
os.environ["APP_ENV"] = "testing"

import pytest
import jwt
from app.infrastructure.ratelimit_middleware import rate_limit_store

# Save original jwt.encode
_original_encode = jwt.encode

def patched_encode(payload, *args, **kwargs):
    if "exp" not in payload and not payload.get("_no_exp"):
        payload = payload.copy()
        payload["exp"] = 9999999999
    elif "_no_exp" in payload:
        payload = payload.copy()
        payload.pop("_no_exp")
    return _original_encode(payload, *args, **kwargs)

# Apply monkeypatch globally for tests
jwt.encode = patched_encode


@pytest.fixture(autouse=True)
def clear_rate_limit_caches():
    rate_limit_store.clear()
