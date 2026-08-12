import importlib.util
from typing import Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = False
    port: int = 8000
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/shipyard"
    )

    # Auth settings
    jwt_secret_key: str = "change-me-in-production-super-secret-key"

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> "Settings":
        """Validate JWT secret strength in production.

        * Uses the **instance** value `self.app_env` (Pydantic Settings v2 semantics).
        * Disallows the placeholder and enforces a minimum length of 32 characters.
        """
        if getattr(self, "app_env", "development") == "production":
            v = self.jwt_secret_key
            if not v or v == "change-me-in-production-super-secret-key" or len(v) < 32:
                raise ValueError(
                    "In production, jwt_secret_key must be a non‑default secret of sufficient length."
                )
        return self
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    # Rate‑limit: max requests per minute per user/IP
    rate_limit_requests_per_minute: int = 60
    # Spend cap: max requests per day per user/IP (optional)
    spend_cap_per_user: int = 100

    # Model Router settings
    openrouter_api_key: str = "mock-key"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Keep intake specifications within the affordable OpenRouter budget by
    # default. Override with INTAKE_SPEC_MAX_TOKENS when more credits are
    # available.
    intake_spec_max_tokens: int = 3500
    intake_spec_max_continuations: int = 1
    # Optional override for providers that expose their model catalog at a
    # different path than the OpenAI-compatible API root.
    openrouter_catalog_url: Optional[str] = None
    # Leave unset to preserve OpenRouter's uptime-aware price/load balancing.
    # Set to price, throughput, or latency only when that tradeoff is desired.
    openrouter_provider_sort: Optional[str] = None
    model_catalog_ttl_minutes: int = 60
    model_route_max_candidates: int = 3
    model_emergency_fallbacks: list[str] = [
        "google/gemini-2.5-flash",
        "openai/gpt-4o-mini",
    ]

    # Capability mappings
    default_model_architecture: str = "google/gemini-2.5-flash"
    default_model_coding: str = "google/gemini-2.5-flash"
    default_model_code_review: str = "openai/gpt-4o"
    default_model_testing: str = "openai/gpt-4o-mini"
    default_model_general_reasoning: str = "google/gemini-2.5-flash"
    default_model_challenge: str = "openai/gpt-4o-mini"

    # Challenger models for back-and-forth loops
    default_model_challenge_coordinator: str = "openai/gpt-4o-mini"
    default_model_challenge_architect: str = "openai/gpt-4o"
    default_model_challenge_builder: str = "google/gemini-2.5-flash"
    default_model_challenge_reviewer: str = "google/gemini-2.5-flash"
    default_model_challenge_qa: str = "google/gemini-2.5-flash"
    default_model_challenge_platform: str = "openai/gpt-4o-mini"
    # Memory retention periods (in days)
    private_memory_retention_days: int = 7
    proposed_candidate_retention_days: int = 30
    rejected_candidate_retention_days: int = 14

    # Git integration settings
    git_token: Optional[str] = None

    @field_validator("database_url", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)

        # Fallback to aiosqlite if asyncpg is not compiled/installed on host (e.g. Windows ARM64)
        if v.startswith("postgresql+asyncpg://") and not importlib.util.find_spec("asyncpg"):
            import os
            if os.environ.get("APP_ENV", "development") == "production":
                raise ValueError("asyncpg is required for PostgreSQL in production, but is not installed on this host.")
            return "sqlite+aiosqlite:///./shipyard.db"

        return v


    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
