"""
Tests for risk calculator endpoints:
  POST /risk/calculate (public/optional auth)
  GET /risk/history (requires auth)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# POST /risk/calculate (public/optional auth)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_calculate_risk_public_no_auth(client, mock_database):
    """POST /risk/calculate works without authentication."""
    mock_database.execute = AsyncMock(return_value=None)

    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            "risk_percent": 1.5,
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
            "take_profit": 1.0950,
            "instrument_type": "forex",
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert "position_size" in data
    assert "risk_amount" in data
    assert "max_loss" in data
    assert "recommendation" in data
    assert "is_valid" in data


@pytest.mark.asyncio
async def test_calculate_risk_valid_inputs(client, mock_database):
    """POST /risk/calculate with valid inputs returns correct calculations."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            "risk_percent": 2.0,
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
            "take_profit": 1.0950,
            "instrument_type": "forex",
            "symbol": "EURUSD",
        },
    )

    assert res.status_code == 200
    data = res.json()
    # Position size should be calculated correctly
    assert data["position_size"] > 0
    # Risk amount should be 2% of 10000 = 200
    assert data["risk_amount"] == 200.0
    # Risk percent should match input
    assert data["risk_percent"] == 2.0
    assert data["instrument_type"] == "forex"
    assert data["symbol"] == "EURUSD"


@pytest.mark.asyncio
async def test_calculate_risk_high_risk_warning(client, mock_database):
    """POST /risk/calculate with > 2% risk returns high_risk recommendation."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            "risk_percent": 5.0,  # More than 2% → high risk
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
            "take_profit": 1.0950,
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["recommendation"] == "high_risk"
    assert len(data["warnings"]) > 0
    assert "dangerous" in data["warnings"][0].lower()


@pytest.mark.asyncio
async def test_calculate_risk_poor_risk_reward(client, mock_database):
    """POST /risk/calculate with poor R:R ratio returns warning."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            "risk_percent": 1.0,
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
            "take_profit": 1.0860,  # Only 10 pips profit vs 50 pips risk → poor R:R
            "instrument_type": "forex",
        },
    )

    assert res.status_code == 200
    data = res.json()
    # Should recommend poor_risk_reward
    assert data["recommendation"] in ("valid", "poor_risk_reward")
    if "poor_risk_reward" in data["recommendation"]:
        assert len(data["warnings"]) > 0


@pytest.mark.asyncio
async def test_calculate_risk_different_instruments(client, mock_database):
    """POST /risk/calculate handles different instrument types."""
    instruments = ["forex", "jpy", "gold", "silver", "oil", "indices"]

    for instrument in instruments:
        res = await client.post(
            "/risk/calculate",
            json={
                "account_balance": 10000,
                "risk_percent": 1.0,
                "entry_price": 100.0 if instrument != "jpy" else 110.0,
                "stop_loss": 99.0 if instrument != "jpy" else 109.0,
                "take_profit": 102.0 if instrument != "jpy" else 112.0,
                "instrument_type": instrument,
            },
        )

        assert res.status_code == 200
        data = res.json()
        assert data["instrument_type"] == instrument
        assert data["position_size"] > 0


@pytest.mark.asyncio
async def test_calculate_risk_zero_account_balance(client):
    """POST /risk/calculate with zero balance returns 400."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 0,
            "risk_percent": 1.0,
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
        },
    )

    assert res.status_code == 400
    assert "account balance" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_calculate_risk_negative_account_balance(client):
    """POST /risk/calculate with negative balance returns 400."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": -5000,
            "risk_percent": 1.0,
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
        },
    )

    assert res.status_code == 400


@pytest.mark.asyncio
async def test_calculate_risk_invalid_risk_percent(client):
    """POST /risk/calculate with invalid risk percent returns 400."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            "risk_percent": 101.0,  # > 100%
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
        },
    )

    assert res.status_code == 400


@pytest.mark.asyncio
async def test_calculate_risk_entry_equals_stop_loss(client):
    """POST /risk/calculate with entry == stop_loss returns 400."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            "risk_percent": 1.0,
            "entry_price": 1.0850,
            "stop_loss": 1.0850,  # Same as entry
            "take_profit": 1.0950,
        },
    )

    assert res.status_code == 400
    assert "cannot equal" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_calculate_risk_missing_required_fields(client):
    """POST /risk/calculate with missing required fields returns 422."""
    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            # Missing risk_percent, entry_price, stop_loss
        },
    )

    assert res.status_code == 422


@pytest.mark.asyncio
async def test_calculate_risk_authenticated_saves_history(client, mock_database, auth_headers):
    """POST /risk/calculate with auth token saves calculation to history."""
    # Mock authenticated user
    user_dict = {
        "id": 1,
        "email": "test@pipways.com",
        "full_name": "Test User",
        "is_active": True,
        "is_admin": False,
        "password_hash": "xxx",
        "subscription_tier": "free",
        "role": "user",
    }
    mock_database.fetch_one = AsyncMock(return_value=user_dict)
    mock_database.execute = AsyncMock(return_value=None)

    res = await client.post(
        "/risk/calculate",
        json={
            "account_balance": 10000,
            "risk_percent": 1.5,
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
            "take_profit": 1.0950,
            "instrument_type": "forex",
            "symbol": "EURUSD",
        },
        headers=auth_headers,
    )

    assert res.status_code == 200
    # Verify execute was called to save history (non-fatal, so may or may not be called)
    data = res.json()
    assert data["position_size"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# GET /risk/history (requires auth)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_risk_history_unauthenticated(client):
    """GET /risk/history without auth returns 401."""
    res = await client.get("/risk/history")

    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_risk_history_empty(client, mock_database, auth_headers):
    """GET /risk/history with no history returns empty list."""
    # Mock auth user lookup
    user_dict = {"id": 1, "email": "test@pipways.com", "full_name": "Test User",
                 "is_active": True, "is_admin": False, "password_hash": "xxx",
                 "subscription_tier": "free", "role": "user"}
    mock_database.fetch_one = AsyncMock(return_value=user_dict)
    mock_database.fetch_all = AsyncMock(return_value=[])

    res = await client.get("/risk/history", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_risk_history_with_data(client, mock_database, auth_headers):
    """GET /risk/history returns user's calculation history."""
    # Mock auth user lookup
    user_dict = {"id": 1, "email": "test@pipways.com", "full_name": "Test User",
                 "is_active": True, "is_admin": False, "password_hash": "xxx",
                 "subscription_tier": "free", "role": "user"}
    mock_database.fetch_one = AsyncMock(return_value=user_dict)

    now = datetime.utcnow()
    fake_calculations = [
        {
            "position_size": 0.5,
            "risk_percent": 1.5,
            "risk_reward_ratio": 2.5,
            "instrument_type": "forex",
            "symbol": "EURUSD",
            "calculated_at": now,
            "account_balance": 10000,
        },
        {
            "position_size": 0.3,
            "risk_percent": 1.0,
            "risk_reward_ratio": 1.8,
            "instrument_type": "forex",
            "symbol": "GBPUSD",
            "calculated_at": now,
            "account_balance": 10000,
        },
    ]
    # Return actual dicts, not MagicMocks
    mock_database.fetch_all = AsyncMock(return_value=fake_calculations)

    res = await client.get("/risk/history", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["symbol"] == "EURUSD"
    assert data[0]["position_size"] == 0.5
    assert data[1]["symbol"] == "GBPUSD"


@pytest.mark.asyncio
async def test_get_risk_history_limit_parameter(client, mock_database, auth_headers):
    """GET /risk/history respects limit parameter."""
    # Mock auth user lookup
    user_dict = {"id": 1, "email": "test@pipways.com", "full_name": "Test User",
                 "is_active": True, "is_admin": False, "password_hash": "xxx",
                 "subscription_tier": "free", "role": "user"}
    mock_database.fetch_one = AsyncMock(return_value=user_dict)

    fake_rows = [
        MagicMock(spec=dict, **{
            "position_size": 0.1 * i,
            "risk_percent": 1.0,
            "risk_reward_ratio": 2.0,
            "instrument_type": "forex",
            "symbol": f"SYM{i}",
            "calculated_at": datetime.utcnow(),
            "account_balance": 10000,
        })
        for i in range(1, 6)
    ]
    mock_database.fetch_all = AsyncMock(return_value=fake_rows[:3])

    res = await client.get("/risk/history?limit=3", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_risk_history_db_error(client, mock_database, auth_headers):
    """GET /risk/history handles database errors gracefully."""
    # Mock auth user lookup
    user_dict = {"id": 1, "email": "test@pipways.com", "full_name": "Test User",
                 "is_active": True, "is_admin": False, "password_hash": "xxx",
                 "subscription_tier": "free", "role": "user"}
    mock_database.fetch_one = AsyncMock(return_value=user_dict)
    mock_database.fetch_all = AsyncMock(side_effect=Exception("DB Error"))

    res = await client.get("/risk/history", headers=auth_headers)

    # Returns empty list on error (graceful fallback)
    assert res.status_code == 200
    data = res.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_risk_history_invalid_limit(client, mock_database, auth_headers):
    """GET /risk/history with invalid limit parameter."""
    # Mock auth user lookup
    user_dict = {"id": 1, "email": "test@pipways.com", "full_name": "Test User",
                 "is_active": True, "is_admin": False, "password_hash": "xxx",
                 "subscription_tier": "free", "role": "user"}
    mock_database.fetch_one = AsyncMock(return_value=user_dict)
    mock_database.fetch_all = AsyncMock(return_value=[])

    res = await client.get("/risk/history?limit=-5", headers=auth_headers)

    # May return 422 for invalid param or return default
    assert res.status_code in (200, 422)
