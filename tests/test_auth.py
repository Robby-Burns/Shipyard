from fastapi.testclient import TestClient
import jwt
from app.config.settings import settings
from app.main import app

client = TestClient(app)


def test_unauthenticated_access():
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authentication credentials"
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


def test_invalid_token_access():
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer invalid.token.payload"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_valid_token_access():
    payload = {"sub": "user_123", "email": "user@example.com", "role": "admin", "exp": 9999999999}
    token = jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"user": payload}
    assert "X-Request-ID" in response.headers


def test_custom_request_id_tracing():
    custom_id = "test-request-id-12345"
    response = client.get("/healthz", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
