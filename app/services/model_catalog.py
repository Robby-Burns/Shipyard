from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config.settings import settings
from app.database.models.model_routing import ModelCatalogSnapshot

logger = structlog.get_logger()


def _api_root(base_url: str) -> str:
    root = base_url.rstrip("/")
    for suffix in ("/chat/completions", "/models"):
        if root.endswith(suffix):
            return root[: -len(suffix)]
    return root


class ModelCatalogService:
    """Discover and cache provider models without making routing depend on catalog uptime."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_candidates(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if not force_refresh:
            cached = await self._read_cached(now, include_expired=False)
            if cached:
                return cached

        if settings.openrouter_api_key == "mock-key":
            return self._emergency_candidates()

        try:
            models = await self._fetch_catalog()
            if models:
                await self._save_catalog(models, now)
                return models
        except Exception as exc:
            logger.warning("model_catalog_refresh_failed", error=str(exc))

        # A provider catalog outage must not make the entire application fail.
        stale = await self._read_cached(now, include_expired=True)
        return stale or self._emergency_candidates()

    async def mark_unavailable(self, model_id: str) -> None:
        await self.db.execute(
            update(ModelCatalogSnapshot)
            .where(
                ModelCatalogSnapshot.provider == "openrouter",
                ModelCatalogSnapshot.model_id == model_id,
            )
            .values(is_available=False)
        )
        await self.db.commit()

    async def _fetch_catalog(self) -> List[Dict[str, Any]]:
        url = settings.openrouter_catalog_url or f"{_api_root(settings.openrouter_base_url)}/models"
        headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params={
                    "output_modalities": "text",
                    "limit": 1000,
                },
                timeout=15.0,
            )
            response.raise_for_status()
            payload = response.json()

        models = [self._normalize_model(item) for item in payload.get("data", [])]
        return [
            model
            for model in models
            if model.get("model_id") and self._is_interactive_model(model)
        ]

    async def _read_cached(
        self, now: datetime, include_expired: bool
    ) -> List[Dict[str, Any]]:
        query = select(ModelCatalogSnapshot).where(
            ModelCatalogSnapshot.provider == "openrouter",
            ModelCatalogSnapshot.is_available.is_(True),
        )
        if not include_expired:
            query = query.where(ModelCatalogSnapshot.expires_at > now)
        result = await self.db.execute(query)
        return [
            self._snapshot_to_dict(row)
            for row in result.scalars().all()
            if self._is_interactive_model(self._snapshot_to_dict(row))
        ]

    async def _save_catalog(self, models: List[Dict[str, Any]], fetched_at: datetime) -> None:
        await self.db.execute(
            update(ModelCatalogSnapshot)
            .where(ModelCatalogSnapshot.provider == "openrouter")
            .values(is_available=False)
        )
        expires_at = fetched_at + timedelta(minutes=settings.model_catalog_ttl_minutes)
        for model in models:
            result = await self.db.execute(
                select(ModelCatalogSnapshot).where(
                    ModelCatalogSnapshot.provider == "openrouter",
                    ModelCatalogSnapshot.model_id == model["model_id"],
                )
            )
            snapshot = result.scalar_one_or_none()
            values = {
                **model,
                "provider": "openrouter",
                "fetched_at": fetched_at,
                "expires_at": expires_at,
                "is_available": True,
            }
            if snapshot:
                for key, value in values.items():
                    setattr(snapshot, key, value)
            else:
                self.db.add(ModelCatalogSnapshot(**values))
        await self.db.commit()

    @staticmethod
    def _normalize_model(item: Dict[str, Any]) -> Dict[str, Any]:
        pricing = item.get("pricing") or {}
        top_provider = item.get("top_provider") or {}

        def price_per_million(value: Any) -> float:
            try:
                return float(value or 0) * 1_000_000
            except (TypeError, ValueError):
                return 0.0

        return {
            "model_id": item.get("id") or item.get("canonical_slug"),
            "model_name": item.get("name"),
            "context_length": item.get("context_length"),
            "max_completion_tokens": top_provider.get("max_completion_tokens"),
            "input_price_per_million": price_per_million(pricing.get("prompt")),
            "output_price_per_million": price_per_million(pricing.get("completion")),
            "supported_parameters": item.get("supported_parameters") or [],
            "benchmarks": item.get("benchmarks") or {},
            "raw_metadata": item,
        }

    @staticmethod
    def _snapshot_to_dict(row: ModelCatalogSnapshot) -> Dict[str, Any]:
        return {
            "model_id": row.model_id,
            "model_name": row.model_name,
            "context_length": row.context_length,
            "max_completion_tokens": row.max_completion_tokens,
            "input_price_per_million": row.input_price_per_million or 0.0,
            "output_price_per_million": row.output_price_per_million or 0.0,
            "supported_parameters": row.supported_parameters or [],
            "benchmarks": row.benchmarks or {},
            "architecture": (row.raw_metadata or {}).get("architecture") or {},
            "raw_metadata": row.raw_metadata or {},
        }

    @staticmethod
    def _is_interactive_model(model: Dict[str, Any]) -> bool:
        """Exclude catalog entries that cannot serve chat completions."""
        model_id = str(model.get("model_id") or "").lower()
        if model_id.endswith(":batch") or model_id.endswith("/batch") or model_id.endswith("-batch"):
            return False

        raw_metadata = model.get("raw_metadata") or {}
        architecture = model.get("architecture") or raw_metadata.get("architecture") or {}
        output_modalities = architecture.get("output_modalities") or []
        if output_modalities and "text" not in output_modalities:
            return False
        supported_parameters = set(model.get("supported_parameters") or [])
        if raw_metadata and not supported_parameters.intersection(
            {"max_tokens", "max_completion_tokens"}
        ):
            return False

        raw = raw_metadata
        searchable = " ".join(
            str(raw.get(field) or "")
            for field in ("id", "canonical_slug", "name", "description", "endpoint_type")
        ).lower()
        batch_markers = (
            "batch-only",
            "batch only",
            "only available through batch",
            "only available through the batch api",
            "batch api only",
            "available only through batch",
            "only supports batch",
        )
        return not any(marker in searchable for marker in batch_markers)

    @staticmethod
    def _emergency_candidates() -> List[Dict[str, Any]]:
        return [
            {
                "model_id": model_id,
                "model_name": model_id,
                "context_length": None,
                "max_completion_tokens": None,
                "input_price_per_million": 0.0,
                "output_price_per_million": 0.0,
                "supported_parameters": [],
                "benchmarks": {},
                "raw_metadata": {},
            }
            for model_id in settings.model_emergency_fallbacks
        ]
