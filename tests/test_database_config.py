from unittest.mock import patch
from app.config.settings import Settings


def test_database_url_normalization_with_asyncpg():
    with patch("importlib.util.find_spec", return_value=True):
        # Neon postgresql:// scheme
        neon_url = "postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require"
        s1 = Settings(database_url=neon_url)
        assert s1.database_url.startswith("postgresql+asyncpg://")
        assert "ep-xyz.us-east-2.aws.neon.tech" in s1.database_url
        assert "sslmode=require" in s1.database_url

        # postgres:// scheme
        s2 = Settings(database_url="postgres://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require")
        assert s2.database_url.startswith("postgresql+asyncpg://")


def test_sqlite_url_normalization():
    # standard sqlite:// scheme
    s1 = Settings(database_url="sqlite:///./shipyard.db")
    assert s1.database_url == "sqlite+aiosqlite:///./shipyard.db"

    # already formatted sqlite+aiosqlite://
    s2 = Settings(database_url="sqlite+aiosqlite:///./shipyard.db")
    assert s2.database_url == "sqlite+aiosqlite:///./shipyard.db"

