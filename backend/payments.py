"""
Pipways — Paystack Payment Integration (Nigeria market)
Replaces Stripe entirely.

Endpoints:
  POST /payments/initiate          — start a subscription checkout
  POST /payments/verify/{ref}      — verify after Paystack redirect
  GET  /payments/plans             — list available plans with Naira pricing
  POST /payments/webhook           — Paystack webhook (charge.success events)

Environment variables required:
  PAYSTACK_SECRET_KEY   — sk_live_... or sk_test_...
  PAYSTACK_PUBLIC_KEY   — pk_live_... or pk_test_...
  APP_URL               — e.g. https://pipways.com (for callback URL)
"""

import os
import hmac
import hashlib
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from .database import database
from .security import get_current_user, get_user_id

router = APIRouter()

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
APP_URL = os.getenv("APP_URL", "https://pipways.com")
PAYSTACK_BASE = "https://api.paystack.co"


# ── Pricing in Naira ─────────────────────────────────────────────────────────
# Trading Academy is FREE for all users — no plan needed for that.
# These plans gate AI tools and pro features only.

PLANS = {
    "pro_monthly": {
        "name":        "Pro Monthly",
        "tier":        "pro",
        "amount_ngn":  20000,
        "amount_kobo": 20000 * 100,
        "interval":    "monthly",
        "description": "Unlimited AI Mentor, Chart Analysis, Performance Analytics, Signals + Telegram",
        "features": [
            "Unlimited AI Mentor sessions",
            "20 Chart Analyses per month",
            "Unlimited Performance Analytics",
            "Full trading signals + Telegram alerts",
            "Webinar recordings access",
        ],
    },
    "pro_yearly": {
        "name":        "Pro Yearly",
        "tier":        "pro",
        "amount_ngn":  200000,
        "amount_kobo": 200000 * 100,
        "interval":    "annually",
        "description": "Everything in Pro, billed yearly. Save \u20a640,000.",
        "features": [
            "Everything in Pro Monthly",
            "Save \u20a640,000 vs monthly billing",
            "Priority AI response speed",
        ],
    },
    "power_monthly": {
        "name":        "Power Trader",
        "tier":        "pro_plus",
        "amount_ngn":  35000,
        "amount_kobo": 35000 * 100,
        "interval":    "monthly",
        "description": "Everything Pro + unlimited Chart Analysis + AI Stock Terminal",
        "features": [
            "Everything in Pro",
            "Unlimited Chart Analyses",
            "AI Stock Research Terminal",
            "Earliest access to new features",
        ],
    },
}


# ── Models ────────────────────────────────────────────────────────────────────

class InitiatePaymentRequest(BaseModel):
    plan_key: str
    coupon: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _headers() -> dict:
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(503, "Payment system not configured. Contact support.")
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


async def _paystack_post(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(f"{PAYSTACK_BASE}{path}", headers=_headers(), json=payload)
    data = res.json()
    if not data.get("status"):
        raise HTTPException(400, data.get("message", "Paystack error"))
    return data


async def _paystack_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(f"{PAYSTACK_BASE}{path}", headers=_headers())
    data = res.json()
    if not data.get("status"):
        raise HTTPException(400, data.get("message", "Paystack error"))
    return data


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/config")
async def get_config():
    """Return Paystack public key for frontend Inline JS."""
    if not PAYSTACK_PUBLIC_KEY:
        raise HTTPException(503, "Payment system not configured")
    return {"public_key": PAYSTACK_PUBLIC_KEY}


@router.get("/plans")
async def get_plans():
    """
    Return all available plans with Naira pricing keyed by plan key.
    Public — no auth required (used on pricing page & subscription section).
    """
    return {
        key: {
            "name":        plan["name"],
            "tier":        plan["tier"],
            "amount_ngn":  plan["amount_ngn"],
            "amount":      plan["amount_kobo"],
            "interval":    plan["interval"],
            "description": plan["description"],
            "features":    plan["features"],
        }
        for key, plan in PLANS.items()
    }


@router.post("/initiate")
async def initiate_payment(
    body: InitiatePaymentRequest,
    current_user=Depends(get_current_user),
):
    """
    Start a Paystack checkout.
    Returns authorization_url — redirect the user there.

    Flow:
      1. POST /payments/initiate  → { authorization_url, reference }
      2. Redirect user to authorization_url
      3. Paystack redirects to APP_URL/payments/callback?reference=...
      4. POST /payments/verify/{reference}  → tier upgraded
    """
    plan = PLANS.get(body.plan_key)
    if not plan:
        raise HTTPException(400, f"Unknown plan: {body.plan_key}. Valid: {list(PLANS.keys())}")

    user_id = get_user_id(current_user)
    email = (
        current_user.get("email") if isinstance(current_user, dict)
        else getattr(current_user, "email", None)
    )
    if not email:
        raise HTTPException(400, "Could not determine user email")

    reference = f"pip_{user_id}_{plan['tier']}_{int(datetime.utcnow().timestamp())}"

    try:
        await database.execute(
            """
            INSERT INTO payment_transactions
                (user_id, reference, plan_key, tier, amount_ngn, status, created_at)
            VALUES (:uid, :ref, :plan, :tier, :amount, 'pending', NOW())
            ON CONFLICT (reference) DO NOTHING
            """,
            {"uid": user_id, "ref": reference, "plan": body.plan_key,
             "tier": plan["tier"], "amount": plan["amount_ngn"]},
        )
    except Exception as e:
        print(f"[PAYMENTS] Could not store pending transaction: {e}", flush=True)

    data = await _paystack_post(
        "/transaction/initialize",
        {
            "email":        email,
            "amount":       plan["amount_kobo"],
            "reference":    reference,
            "callback_url": f"{APP_URL}/payments/callback",
            "metadata": {
                "user_id":  user_id,
                "plan_key": body.plan_key,
                "tier":     plan["tier"],
            },
            "channels": ["card", "bank", "ussd", "mobile_money", "bank_transfer"],
        },
    )

    return {
        "authorization_url": data["data"]["authorization_url"],
        "reference":         data["data"]["reference"],
        "plan":              plan["name"],
        "amount_ngn":        plan["amount_ngn"],
    }


@router.post("/verify/{reference}")
async def verify_payment(reference: str, current_user=Depends(get_current_user)):
    """
    Verify a Paystack payment after redirect.
    Upgrades the user's subscription_tier on success.
    """
    user_id = get_user_id(current_user)
    data = await _paystack_get(f"/transaction/verify/{reference}")
    tx = data["data"]

    if tx["status"] != "success":
        raise HTTPException(400, f"Payment not successful. Status: {tx['status']}")

    meta = tx.get("metadata", {})
    plan_key = meta.get("plan_key")
    tier = meta.get("tier") or (PLANS.get(plan_key, {}).get("tier") if plan_key else None)
    if not tier:
        raise HTTPException(400, "Could not determine tier from payment metadata")

    await _upgrade_user(user_id, tier, reference)

    return {
        "success":   True,
        "tier":      tier,
        "reference": reference,
        "message":   f"Payment verified. You now have {tier} access.",
    }


@router.post("/webhook")
async def paystack_webhook(request: Request):
    """
    Paystack webhook for charge.success events.
    Add this URL in Paystack dashboard → Settings → Webhooks:
      https://pipways.com/payments/webhook
    """
    signature = request.headers.get("x-paystack-signature", "")
    body_bytes = await request.body()

    if not PAYSTACK_SECRET_KEY:
        print("[PAYMENTS] ⚠️ PAYSTACK_SECRET_KEY not set — rejecting webhook", flush=True)
        raise HTTPException(503, "Payment system not configured")

    expected = hmac.new(
        PAYSTACK_SECRET_KEY.encode("utf-8"),
        body_bytes,
        hashlib.sha512,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(400, "Invalid webhook signature")

    payload = json.loads(body_bytes)

    if payload.get("event") == "charge.success":
        tx_data = payload.get("data", {})
        reference = tx_data.get("reference", "")
        meta = tx_data.get("metadata", {})
        user_id = meta.get("user_id")
        plan_key = meta.get("plan_key")
        tier = meta.get("tier") or (PLANS.get(plan_key, {}).get("tier") if plan_key else None)

        if user_id and tier:
            await _upgrade_user(int(user_id), tier, reference)
            print(f"[PAYMENTS] Webhook: upgraded user {user_id} to {tier}", flush=True)

    return {"status": "ok"}


# ── Internal ──────────────────────────────────────────────────────────────────

async def _upgrade_user(user_id: int, tier: str, reference: str) -> None:
    """Upgrade user tier. Idempotent — safe to call from /verify and /webhook."""
    try:
        await database.execute(
            """UPDATE users SET subscription_tier = :tier,
               subscription_updated_at = NOW() WHERE id = :uid""",
            {"tier": tier, "uid": user_id},
        )
    except Exception:
        try:
            await database.execute(
                "UPDATE users SET subscription_tier = :tier WHERE id = :uid",
                {"tier": tier, "uid": user_id},
            )
        except Exception as e:
            print(f"[PAYMENTS] Failed to upgrade user {user_id}: {e}", flush=True)
            return

    try:
        await database.execute(
            """UPDATE payment_transactions SET status='completed', completed_at=NOW()
               WHERE reference=:ref""",
            {"ref": reference},
        )
    except Exception as e:
        print(f"[PAYMENTS] Could not update transaction status: {e}", flush=True)

    print(f"[PAYMENTS] User {user_id} upgraded to {tier} (ref: {reference})", flush=True)


async def init_payment_tables():
    """Create payment_transactions table. Call from main.py lifespan."""
    try:
        await database.execute("""
            CREATE TABLE IF NOT EXISTS payment_transactions (
                id           SERIAL PRIMARY KEY,
                user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                reference    VARCHAR(120) UNIQUE NOT NULL,
                plan_key     VARCHAR(60) NOT NULL,
                tier         VARCHAR(30) NOT NULL,
                amount_ngn   INTEGER NOT NULL,
                status       VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """)
        await database.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_updated_at TIMESTAMP"
        )
        print("[PAYMENTS] Payment tables ready.", flush=True)
    except Exception as e:
        print(f"[PAYMENTS] Table init warning: {e}", flush=True)
