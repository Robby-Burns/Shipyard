from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import get_db
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Shipyard Platform Operational",
        "env": "development",
    }


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_database_offline_or_connected():
    response = client.get("/readyz")
    if response.status_code == 503:
        assert "Database connection failed" in response.json()["detail"]
    else:
        assert response.status_code == 200
        assert response.json() == {"status": "ready", "database": "connected"}


def test_readyz_with_mock_db():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/readyz")
        assert response.status_code == 200
        assert response.json() == {"status": "ready", "database": "connected"}
    finally:
        app.dependency_overrides.clear()
