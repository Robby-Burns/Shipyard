from datetime import datetime, timezone

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.session import Base
from app.database.models.model_routing import ModelCatalogSnapshot
from app.services.model_catalog import ModelCatalogService, _api_root


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


def test_catalog_api_root_handles_configured_endpoint():
    assert _api_root("https://openrouter.ai/api/v1") == "https://openrouter.ai/api/v1"
    assert _api_root("https://openrouter.ai/api/v1/chat/completions") == "https://openrouter.ai/api/v1"
    assert _api_root("https://openrouter.ai/api/v1/models") == "https://openrouter.ai/api/v1"


@pytest.mark.anyio
async def test_catalog_uses_emergency_candidates_in_mock_mode(async_session, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "mock-key")
    service = ModelCatalogService(async_session)

    candidates = await service.get_candidates()

    assert candidates
    assert candidates[0]["model_id"] in settings.model_emergency_fallbacks


@pytest.mark.anyio
async def test_catalog_reads_cached_snapshot(async_session, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "real-key")
    row = ModelCatalogSnapshot(
        provider="openrouter",
        model_id="google/gemini-2.5-flash",
        model_name="Gemini 2.5 Flash",
        input_price_per_million=0.3,
        output_price_per_million=2.5,
        supported_parameters=["max_tokens"],
        fetched_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc).replace(year=2099),
        is_available=True,
    )
    async_session.add(row)
    await async_session.commit()

    candidates = await ModelCatalogService(async_session).get_candidates()

    assert candidates[0]["model_id"] == "google/gemini-2.5-flash"


@pytest.mark.anyio
async def test_catalog_url_can_be_configured_independently(async_session, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "real-key")
    monkeypatch.setattr(
        settings, "openrouter_catalog_url", "https://catalog.example.test/v2"
    )
    requested_urls = []

    async def mock_get(self, url, **kwargs):
        requested_urls.append(url)
        return httpx.Response(
            200,
            json={"data": [{"id": "example/model", "pricing": {}}]},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    await ModelCatalogService(async_session).get_candidates(force_refresh=True)

    assert requested_urls == ["https://catalog.example.test/v2"]
