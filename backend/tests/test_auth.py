"""
Tests for authentication endpoints: /auth/register, /auth/token, /auth/me
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.security import get_password_hash


# ═══════════════════════════════════════════════════════════════════════════════
# POST /auth/register
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_register_success(client, mock_database):
    """New user registration returns 200 with access token."""
    # get_user_by_email returns None (no existing user)
    mock_database.fetch_one = AsyncMock(return_value=None)
    # create_user insert returns a user id
    mock_database.execute = AsyncMock(return_value=1)

    # Patch get_available_columns to avoid real DB inspection
    with patch("backend.auth.get_columns", return_value=[
        "email", "password_hash", "full_name", "is_active",
        "is_admin", "role", "subscription_tier", "created_at",
    ]):
        res = await client.post("/auth/register", json={
            "email": "new@pipways.com",
            "password": "StrongPass123!",
            "full_name": "Test User",
        })

    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "new@pipways.com"
    assert data["user"]["subscription_tier"] == "free"


@pytest.mark.asyncio
async def test_register_duplicate_email(client, mock_database):
    """Registration with existing email returns 400."""
    # Simulate existing user found
    mock_database.fetch_one = AsyncMock(return_value={"id": 1, "email": "dup@pipways.com"})

    res = await client.post("/auth/register", json={
        "email": "dup@pipways.com",
        "password": "StrongPass123!",
        "full_name": "Dup User",
    })

    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    """Registration with malformed email returns 422."""
    res = await client.post("/auth/register", json={
        "email": "not-an-email",
        "password": "StrongPass123!",
        "full_name": "Bad Email",
    })
    assert res.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /auth/token  (login)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_login_success(client, mock_database):
    """Valid credentials return access token."""
    hashed = get_password_hash("CorrectPassword1!")

    # Return a mock user row
    fake_user = MagicMock()
    fake_user.__getitem__ = lambda self, k: {
        "id": 1, "email": "user@pipways.com", "full_name": "Test",
        "is_active": True, "is_admin": False, "password_hash": hashed,
        "subscription_tier": "free", "role": "user",
    }[k]
    fake_user.__contains__ = lambda self, k: True
    for attr, val in {"id": 1, "email": "user@pipways.com", "full_name": "Test",
                      "is_active": True, "is_admin": False, "password_hash": hashed,
                      "subscription_tier": "free", "role": "user"}.items():
        setattr(fake_user, attr, val)

    mock_database.fetch_one = AsyncMock(return_value=fake_user)

    res = await client.post("/auth/token", data={
        "username": "user@pipways.com",
        "password": "CorrectPassword1!",
    })

    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "user@pipways.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client, mock_database):
    """Wrong password returns 401."""
    hashed = get_password_hash("RealPassword")

    fake_user = MagicMock()
    for attr, val in {"id": 1, "email": "user@pipways.com", "full_name": "Test",
                      "is_active": True, "is_admin": False, "password_hash": hashed,
                      "subscription_tier": "free", "role": "user"}.items():
        setattr(fake_user, attr, val)

    mock_database.fetch_one = AsyncMock(return_value=fake_user)

    res = await client.post("/auth/token", data={
        "username": "user@pipways.com",
        "password": "WrongPassword",
    })

    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client, mock_database):
    """Login for unknown email returns 401."""
    mock_database.fetch_one = AsyncMock(return_value=None)

    res = await client.post("/auth/token", data={
        "username": "ghost@pipways.com",
        "password": "Whatever",
    })

    assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# GET /auth/me
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    """Accessing /auth/me without a token returns 401."""
    res = await client.get("/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client, mock_database, auth_headers):
    """Authenticated request to /auth/me returns user profile."""
    fake_user = MagicMock()
    fake_user._mapping = {
        "id": 1, "email": "test@pipways.com", "full_name": "Test User",
        "is_active": True, "is_admin": False, "password_hash": "xxx",
        "subscription_tier": "free", "role": "user",
    }
    fake_user._mapping.get = fake_user._mapping.get
    for attr, val in fake_user._mapping.items():
        setattr(fake_user, attr, val)

    mock_database.fetch_one = AsyncMock(return_value=fake_user)

    res = await client.get("/auth/me", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@pipways.com"
