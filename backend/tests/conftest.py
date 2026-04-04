"""
Shared fixtures for Pipways tests.

Uses httpx.ASGITransport so tests hit the real FastAPI app
without needing a running server or live database.
The database is mocked at the `backend.database.database` level.
"""
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Set required env vars BEFORE any app code is imported
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod-0123456789abcdef")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

import httpx
from httpx import ASGITransport

from backend.security import create_access_token


@pytest.fixture
def mock_database():
    """
    Patch the shared `database` object so no real PostgreSQL is needed.
    Individual tests can configure return values via the yielded mock.
    """
    with patch("backend.database.database") as db_mock:
        db_mock.fetch_one = AsyncMock(return_value=None)
        db_mock.fetch_all = AsyncMock(return_value=[])
        db_mock.execute = AsyncMock(return_value=1)
        db_mock.connect = AsyncMock()
        db_mock.disconnect = AsyncMock()
        yield db_mock


@pytest_asyncio.fixture
async def client(mock_database):
    """
    Async test client that talks to the FastAPI app over ASGI transport.
    Lifespan is disabled so startup migrations don't run against the mock.
    """
    from backend.main import app

    # Disable lifespan so init_database / migrations don't fire
    app.router.lifespan_context = _null_lifespan

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Return Bearer headers for a fake authenticated user."""
    token = create_access_token(data={"sub": "test@pipways.com", "user_id": 1})
    return {"Authorization": f"Bearer {token}"}


# ── Helpers ──────────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager

@asynccontextmanager
async def _null_lifespan(app):
    yield
