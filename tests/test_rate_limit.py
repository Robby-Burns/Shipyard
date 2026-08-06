from fastapi.testclient import TestClient
import jwt
import pytest
from app.config.settings import settings
from app.main import app
from app.infrastructure.ratelimit_middleware import _cache, _spend

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_caches():
    _cache.clear()
    _spend.clear()

def test_rate_limiting_under_limit():
    token = jwt.encode(
        {"sub": "user_rl_1", "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    headers = {"Authorization": f"Bearer {token}"}
    
    # We should be able to make 3 requests fine since limit is 60
    for _ in range(3):
        response = client.get("/healthz", headers=headers)
        assert response.status_code == 200

def test_rate_limiting_exceeded():
    # Set limit low temporarily
    original_limit = settings.rate_limit_requests_per_minute
    settings.rate_limit_requests_per_minute = 2
    try:
        token = jwt.encode(
            {"sub": "user_rl_2", "exp": 9999999999},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1st request -> ok
        assert client.get("/healthz", headers=headers).status_code == 200
        # 2nd request -> ok
        assert client.get("/healthz", headers=headers).status_code == 200
        # 3rd request -> rate limit exceeded
        response = client.get("/healthz", headers=headers)
        assert response.status_code == 429
        assert "rate limit exceeded" in response.json()["detail"]
    finally:
        settings.rate_limit_requests_per_minute = original_limit

def test_spend_cap_exceeded():
    original_cap = settings.spend_cap_per_user
    settings.spend_cap_per_user = 2
    try:
        token = jwt.encode(
            {"sub": "user_sc_1", "exp": 9999999999},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1st request -> ok
        assert client.get("/healthz", headers=headers).status_code == 200
        # 2nd request -> ok
        assert client.get("/healthz", headers=headers).status_code == 200
        # 3rd request -> spend cap exceeded
        response = client.get("/healthz", headers=headers)
        assert response.status_code == 429
        assert "Spend cap exceeded" in response.json()["detail"]
    finally:
        settings.spend_cap_per_user = original_cap

def test_admin_routes_bypass_rate_limiting():
    # Set limit low
    original_limit = settings.rate_limit_requests_per_minute
    settings.rate_limit_requests_per_minute = 1
    try:
        token = jwt.encode(
            {"sub": "admin_user", "exp": 9999999999},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        headers = {"Authorization": f"Bearer {token}"}
        
        # Call non-admin route to consume token
        assert client.get("/healthz", headers=headers).status_code == 200
        # Next call to non-admin route fails
        assert client.get("/healthz", headers=headers).status_code == 429
        
        # Call to admin route should bypass rate limiting.
        # /admin/healthz or similar route doesn't need to exist, just check that it doesn't return 429.
        # If it returns 404, it means it bypassed the 429 rate limiter and reached the router!
        response = client.get("/admin/any-route", headers=headers)
        assert response.status_code != 429
    finally:
        settings.rate_limit_requests_per_minute = original_limit
