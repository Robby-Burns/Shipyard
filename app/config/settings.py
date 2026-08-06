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
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

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
