import importlib.util
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    debug: bool = True
    port: int = 8000
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/shipyard"
    )

    # Auth settings
    jwt_secret_key: str = "change-me-in-production-super-secret-key"

    @field_validator("jwt_secret_key", mode="after")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret strength in production.

        Disallow the default placeholder and enforce a minimum length.
        """
        if getattr(cls, "app_env", "development") == "production":
            if not v or v == "change-me-in-production-super-secret-key" or len(v) < 32:
                raise ValueError(
                    "In production, jwt_secret_key must be a non‑default secret of sufficient length."
                )
        return v
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

    # Capability mappings
    default_model_architecture: str = "anthropic/claude-3.5-sonnet"
    default_model_coding: str = "anthropic/claude-3.5-sonnet"
    default_model_code_review: str = "openai/gpt-4o"
    default_model_testing: str = "openai/gpt-4o-mini"
    default_model_general_reasoning: str = "google/gemini-2.5-flash"

    # Memory retention periods (in days)
    private_memory_retention_days: int = 7
    proposed_candidate_retention_days: int = 30
    rejected_candidate_retention_days: int = 14

    @field_validator("database_url", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)

        # Fallback to aiosqlite if asyncpg is not compiled/installed on host (e.g. Windows ARM64)
        if v.startswith("postgresql+asyncpg://") and not importlib.util.find_spec("asyncpg"):
            return "sqlite+aiosqlite:///./shipyard.db"

        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
