import pytest
import jwt
from pydantic import ValidationError
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config.settings import Settings, settings
from app.utils.url_sanitizer import sanitize_db_url
from app.main import app

client = TestClient(app)


# ==========================================
# 1. Settings Validator Tests (#1)
# ==========================================

def test_settings_validator_production_invalid():
    with pytest.raises(ValidationError) as exc_info:
        Settings(app_env="production", jwt_secret_key="short")
    assert "jwt_secret_key" in str(exc_info.value)


def test_settings_validator_production_default_secret():
    with pytest.raises(ValidationError) as exc_info:
        Settings(app_env="production", jwt_secret_key="change-me-in-production-super-secret-key")
    assert "jwt_secret_key" in str(exc_info.value)


def test_settings_validator_production_valid():
    settings_instance = Settings(
        app_env="production",
        jwt_secret_key="a" * 32
    )
    assert settings_instance.jwt_secret_key == "a" * 32


def test_settings_validator_development_any():
    settings_instance = Settings(
        app_env="development",
        jwt_secret_key="short"
    )
    assert settings_instance.jwt_secret_key == "short"


# ==========================================
# 2. URL Sanitization Tests (#2/#3)
# ==========================================

@pytest.mark.parametrize(
    "input_url,expected_url",
    [
        # URL with @ in password
        ("postgresql://user:pass@word@host:5432/db", "postgresql://user:***@host:5432/db"),
        # URL with multiple @ in password/username
        ("postgresql://user@name:p@ss@w@rd@host:5432/db", "postgresql://user@name:***@host:5432/db"),
        # URL with missing scheme
        ("user:pass@host:5432/db", "user:***@host:5432/db"),
        # SQLite URL (no credentials)
        ("sqlite+aiosqlite:///./shipyard.db", "sqlite+aiosqlite:///./shipyard.db"),
        # In-memory SQLite
        ("sqlite:///:memory:", "sqlite:///:memory:"),
        # Simple postgres URL without password but with username
        ("postgresql://user@host:5432/db", "postgresql://***@host:5432/db"),
    ]
)
def test_sanitize_db_url(input_url, expected_url):
    assert sanitize_db_url(input_url) == expected_url


# ==========================================
# 3. DB Health Check Tests (#4/#6)
# ==========================================

@pytest.mark.anyio
async def test_infrastructure_db_health_healthy(monkeypatch):
    class MockConnection:
        async def execute(self, statement, *args, **kwargs):
            return None

    class MockEngineBegin:
        async def __aenter__(self):
            return MockConnection()
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockEngine:
        def begin(self):
            return MockEngineBegin()

    from app.database import session
    monkeypatch.setattr(session, "engine", MockEngine())

    token = jwt.encode({"sub": "admin"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/infrastructure", headers=headers)
    assert res.status_code == 200
    data = res.json()

    memory_comp = next(c for c in data["components"] if c["name"] == "Memory")
    assert memory_comp["status"] == "Connected"
    assert memory_comp["health"] is True
    # Ensure connection URL is NOT in the details output (Issue #8)
    assert "Connection URL" not in memory_comp["details"]


@pytest.mark.anyio
async def test_infrastructure_db_health_unhealthy(monkeypatch):
    class MockEngineBegin:
        async def __aenter__(self):
            raise Exception("DB Connection Refused")
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockEngine:
        def begin(self):
            return MockEngineBegin()

    from app.database import session
    monkeypatch.setattr(session, "engine", MockEngine())

    token = jwt.encode({"sub": "admin"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/infrastructure", headers=headers)
    assert res.status_code == 200
    data = res.json()

    memory_comp = next(c for c in data["components"] if c["name"] == "Memory")
    assert memory_comp["status"] == "Offline"
    assert memory_comp["health"] is False


# ==========================================
# 4. JWT Expiration Claim Requirement Test (#5)
# ==========================================

def test_jwt_decode_requires_exp():
    # Encode token with _no_exp to bypass the conftest monkeypatch and create a token without 'exp'
    token = jwt.encode({"sub": "user_123", "_no_exp": True}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/infrastructure", headers=headers)
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid or expired token"
