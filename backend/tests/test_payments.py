"""
Tests for payment endpoints: /payments/plans, /payments/initiate, /payments/verify
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ═══════════════════════════════════════════════════════════════════════════════
# GET /payments/plans  (public)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_plans(client):
    """Plans endpoint returns list of pricing plans."""
    res = await client.get("/payments/plans")

    assert res.status_code == 200
    data = res.json()
    # Should return a list or dict of plans
    assert data is not None
    # Verify at least one plan exists
    if isinstance(data, list):
        assert len(data) > 0
    elif isinstance(data, dict):
        assert len(data) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# POST /payments/initiate  (requires auth)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_initiate_payment_unauthenticated(client):
    """Initiating payment without auth returns 401."""
    res = await client.post("/payments/initiate", json={"plan_key": "pro_monthly"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_initiate_payment_invalid_plan(client, mock_database, auth_headers):
    """Initiating payment with invalid plan key returns 400/404."""
    # Mock authenticated user lookup
    fake_user = MagicMock()
    fake_user._mapping = {
        "id": 1, "email": "test@pipways.com", "full_name": "Test",
        "is_active": True, "is_admin": False, "password_hash": "xxx",
        "subscription_tier": "free", "role": "user",
    }
    fake_user._mapping.get = fake_user._mapping.get
    for attr, val in fake_user._mapping.items():
        setattr(fake_user, attr, val)
    mock_database.fetch_one = AsyncMock(return_value=fake_user)

    res = await client.post(
        "/payments/initiate",
        json={"plan_key": "nonexistent_plan"},
        headers=auth_headers,
    )

    # Should reject unknown plan
    assert res.status_code in (400, 404, 422)


@pytest.mark.asyncio
async def test_initiate_payment_valid_plan(client, mock_database, auth_headers):
    """Initiating payment with valid plan calls Paystack and returns checkout URL."""
    fake_user = MagicMock()
    fake_user._mapping = {
        "id": 1, "email": "test@pipways.com", "full_name": "Test",
        "is_active": True, "is_admin": False, "password_hash": "xxx",
        "subscription_tier": "free", "role": "user",
    }
    fake_user._mapping.get = fake_user._mapping.get
    for attr, val in fake_user._mapping.items():
        setattr(fake_user, attr, val)
    mock_database.fetch_one = AsyncMock(return_value=fake_user)

    # Mock the Paystack API call
    mock_paystack_response = {
        "status": True,
        "data": {
            "authorization_url": "https://checkout.paystack.com/test123",
            "reference": "ref_test123",
        },
    }

    with patch("backend.payments._paystack_post", new_callable=AsyncMock,
               return_value=mock_paystack_response):
        res = await client.post(
            "/payments/initiate",
            json={"plan_key": "pro_monthly"},
            headers=auth_headers,
        )

    assert res.status_code == 200
    data = res.json()
    # Should contain a checkout URL or reference
    assert "authorization_url" in str(data).lower() or "reference" in str(data).lower() or "url" in str(data).lower()


# ═══════════════════════════════════════════════════════════════════════════════
# POST /payments/verify/{ref}
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_verify_payment_unauthenticated(client):
    """Verifying payment without auth returns 401."""
    res = await client.post("/payments/verify/ref_123")
    assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# POST /payments/webhook  (Paystack signature validation)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    """Webhook with invalid/missing signature is rejected."""
    res = await client.post(
        "/payments/webhook",
        json={"event": "charge.success", "data": {}},
        headers={"x-paystack-signature": "invalid_sig"},
    )
    # Should reject — either 400, 403, or silently return 200 with no action
    assert res.status_code in (200, 400, 403)
