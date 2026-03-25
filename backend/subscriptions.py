"""
Pipways Subscription & Usage Enforcement — v1.0

Provides:
  • Tier-aware usage limit checking against site_settings
  • check_and_record_usage()  — call at the top of every gated feature route
  • get_usage_state()         — called by /auth/me to return full state to frontend
  • init_subscription_tables()— creates required tables on startup

HTTP 402 is raised when a user hits their tier limit.
The frontend intercepts 402 globally and shows the upgrade modal.

Usage in a route:
    from .subscriptions import check_and_record_usage
    @router.post("/chart/analyse")
    async def analyse(current_user = Depends(get_current_user)):
        await check_and_record_usage(current_user["id"], "chart_analysis")
        # ... rest of handler
"""

from fastapi import HTTPException
from datetime import datetime, date
from typing import Optional
from .database import database


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE CONFIGURATION
# Single source of truth for all tier limits.
# limit_key  → key in site_settings table (admin can edit without redeploy)
# reset      → "lifetime" | "daily" | "monthly"
# default    → fallback if key not found in site_settings
# table      → which DB table stores usage events for this feature
# ═══════════════════════════════════════════════════════════════════════════════

FEATURE_CONFIG = {
    "chart_analysis": {
        "label": "Chart Analysis",
        "free":  {"limit_key": "chart_free_lifetime",   "reset": "lifetime", "default": 2},
        "basic": {"limit_key": "chart_basic_monthly",   "reset": "monthly",  "default": 30},
        "pro":   {"limit_key": "chart_pro_monthly",     "reset": "monthly",  "default": 999},
        "table": "chart_analysis_logs",
    },
    "performance": {
        "label": "Performance Analysis",
        "free":  {"limit_key": "perf_free_lifetime",    "reset": "lifetime", "default": 1},
        "basic": {"limit_key": "perf_basic_monthly",    "reset": "monthly",  "default": 4},
        "pro":   {"limit_key": "perf_pro_monthly",      "reset": "monthly",  "default": 999},
        "table": "journal_uploads",
    },
    "ai_mentor": {
        "label": "AI Mentor",
        "free":  {"limit_key": "mentor_free_daily",     "reset": "daily",    "default": 5},
        "basic": {"limit_key": "mentor_basic_daily",    "reset": "daily",    "default": 25},
        "pro":   {"limit_key": "mentor_pro_daily",      "reset": "daily",    "default": 999},
        "table": "ai_mentor_logs",
    },
    "stock_research": {
        "label": "AI Stock Research",
        "free":  {"limit_key": "stock_free_daily",      "reset": "daily",    "default": 2},
        "basic": {"limit_key": "stock_basic_daily",     "reset": "daily",    "default": 15},
        "pro":   {"limit_key": "stock_pro_daily",       "reset": "daily",    "default": 999},
        "table": "stock_analysis_logs",
    },
}

# Default site_settings values seeded on first init
_DEFAULT_LIMIT_SETTINGS = {
    # Chart Analysis
    "chart_free_lifetime":  "2",
    "chart_basic_monthly":  "30",
    "chart_pro_monthly":    "999",
    # Performance Analysis
    "perf_free_lifetime":   "1",
    "perf_basic_monthly":   "4",
    "perf_pro_monthly":     "999",
    # AI Mentor
    "mentor_free_daily":    "5",
    "mentor_basic_daily":   "25",
    "mentor_pro_daily":     "999",
    # Stock Research
    "stock_free_daily":     "2",
    "stock_basic_daily":    "15",
    "stock_pro_daily":      "999",
}

# Tier display info (used in error responses for frontend upgrade modal)
TIER_INFO = {
    "free":  {"name": "Free",  "price_ngn": None,   "next": "pro"},
    "pro":   {"name": "Pro",   "price_ngn": 15000,  "next": None},
}


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE INIT
# ═══════════════════════════════════════════════════════════════════════════════

async def init_subscription_tables():
    """
    Creates usage log tables for any features that don't have one yet.
    Idempotent — safe to call on every startup.
    Also seeds default limit settings into site_settings.
    """
    # stock_analysis_logs is the only new table — others already exist
    tables = [
        """CREATE TABLE IF NOT EXISTS stock_analysis_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            ticker VARCHAR(50) NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
        # Ensure user_id column exists on existing log tables (migration safety)
        "ALTER TABLE chart_analysis_logs ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE ai_mentor_logs ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE journal_uploads ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
    ]
    for sql in tables:
        try:
            await database.execute(sql)
        except Exception as e:
            print(f"[SUBSCRIPTIONS] table init warning: {e}", flush=True)

    # Ensure site_settings table exists before trying to seed into it
    # (CMS also creates this table, but may run after subscriptions in startup)
    try:
        await database.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                key VARCHAR(120) PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
    except Exception as e:
        print(f"[SUBSCRIPTIONS] site_settings table warning: {e}", flush=True)

    # Seed default limit settings (ON CONFLICT DO NOTHING — never overwrites admin edits)
    for key, value in _DEFAULT_LIMIT_SETTINGS.items():
        try:
            await database.execute(
                """INSERT INTO site_settings (key, value, updated_at)
                   VALUES (:k, :v, NOW())
                   ON CONFLICT (key) DO NOTHING""",
                {"k": key, "v": value},
            )
        except Exception as e:
            print(f"[SUBSCRIPTIONS] settings seed warning: {e}", flush=True)

    print("[SUBSCRIPTIONS] Tables and settings ready.", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def _get_user_tier(user_id: int) -> str:
    """Read the user's subscription_tier from the DB."""
    try:
        row = await database.fetch_one(
            "SELECT subscription_tier FROM users WHERE id = :uid",
            {"uid": user_id},
        )
        if row:
            tier = row["subscription_tier"] or "free"
            # Normalise legacy "enterprise" to "pro"
            return "pro" if tier == "enterprise" else tier
        return "free"
    except Exception as e:
        print(f"[SUBSCRIPTIONS] get tier error user={user_id}: {e}", flush=True)
        return "free"


async def _get_limit(limit_key: str, default: int) -> int:
    """Read a limit value from site_settings, falling back to default."""
    try:
        row = await database.fetch_one(
            "SELECT value FROM site_settings WHERE key = :k",
            {"k": limit_key},
        )
        if row and row["value"] is not None:
            val = int(row["value"])
            return val if val >= 0 else default
        return default
    except Exception:
        return default


def _count_query(table: str, reset: str) -> str:
    """
    Returns a parameterised COUNT query based on reset window.
    :uid is the only parameter needed.
    """
    base = f"SELECT COUNT(*) AS c FROM {table} WHERE user_id = :uid"
    if reset == "lifetime":
        return base
    if reset == "daily":
        return base + " AND created_at >= CURRENT_DATE"
    if reset == "monthly":
        return base + " AND created_at >= DATE_TRUNC('month', NOW())"
    return base


async def _count_usage(user_id: int, table: str, reset: str) -> int:
    """Count how many times user has used a feature within the reset window."""
    try:
        query = _count_query(table, reset)
        row = await database.fetch_one(query, {"uid": user_id})
        return int(row["c"]) if row else 0
    except Exception as e:
        print(f"[SUBSCRIPTIONS] count error table={table}: {e}", flush=True)
        return 0


def _reset_label(reset: str) -> Optional[str]:
    """Human-readable reset cadence for the frontend."""
    return {"daily": "daily", "monthly": "monthly", "lifetime": None}.get(reset)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

async def check_and_record_usage(
    user_id: int,
    feature: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    The main gate function. Call this at the top of every gated route.

    1. Reads user's tier
    2. Reads limit from site_settings (with default fallback)
    3. Counts current usage in the correct window
    4. Raises HTTP 402 if limit reached
    5. Records the usage event if allowed

    Returns a dict with usage info that can be added to the response:
        {"used": 1, "limit": 2, "remaining": 1, "tier": "free"}

    Raises:
        HTTP 402 with JSON body:
        {
            "error": "limit_reached",
            "feature": "chart_analysis",
            "feature_label": "Chart Analysis",
            "used": 2,
            "limit": 2,
            "tier": "free",
            "next_tier": "basic",
            "next_tier_price": 15,
            "resets": null  // or "daily" / "monthly"
        }
    """
    cfg = FEATURE_CONFIG.get(feature)
    if not cfg:
        # Unknown feature — allow through (fail open, don't block unknown routes)
        return {"used": 0, "limit": 999, "remaining": 999, "tier": "free"}

    tier = await _get_user_tier(user_id)

    # Pro users on unlimited features — skip DB queries entirely
    tier_cfg = cfg.get(tier) or cfg.get("free")
    limit = await _get_limit(tier_cfg["limit_key"], tier_cfg["default"])
    reset = tier_cfg["reset"]

    # 999 means unlimited — record but don't check
    if limit < 999:
        used = await _count_usage(user_id, cfg["table"], reset)
        if used >= limit:
            tier_info = TIER_INFO.get(tier, {})
            next_tier = tier_info.get("next")
            next_price = TIER_INFO.get(next_tier, {}).get("price") if next_tier else None
            raise HTTPException(
                status_code=402,
                detail={
                    "error":           "limit_reached",
                    "feature":         feature,
                    "feature_label":   cfg["label"],
                    "used":            used,
                    "limit":           limit,
                    "tier":            tier,
                    "next_tier":       next_tier,
                    "next_tier_price": next_price,
                    "resets":          _reset_label(reset),
                    "upgrade_url":     "/pricing.html",
                },
            )
    else:
        used = await _count_usage(user_id, cfg["table"], reset)

    # Record the usage event
    await _record_usage(user_id, feature, cfg["table"], metadata or {})

    remaining = max(0, limit - used - 1) if limit < 999 else 999
    return {
        "used":      used + 1,
        "limit":     limit,
        "remaining": remaining,
        "tier":      tier,
    }


async def _record_usage(
    user_id: int,
    feature: str,
    table: str,
    metadata: dict,
) -> None:
    """Insert a usage event into the feature's log table."""
    try:
        if table == "chart_analysis_logs":
            await database.execute(
                """INSERT INTO chart_analysis_logs (user_id, created_at)
                   VALUES (:uid, NOW())""",
                {"uid": user_id},
            )
        elif table == "ai_mentor_logs":
            await database.execute(
                """INSERT INTO ai_mentor_logs (user_id, created_at, question_topic)
                   VALUES (:uid, NOW(), :topic)""",
                {"uid": user_id, "topic": metadata.get("topic", "")},
            )
        elif table == "journal_uploads":
            await database.execute(
                """INSERT INTO journal_uploads (user_id, created_at)
                   VALUES (:uid, NOW())""",
                {"uid": user_id},
            )
        elif table == "stock_analysis_logs":
            await database.execute(
                """INSERT INTO stock_analysis_logs (user_id, ticker, created_at)
                   VALUES (:uid, :ticker, NOW())""",
                {"uid": user_id, "ticker": metadata.get("ticker", "")},
            )
    except Exception as e:
        # Non-fatal: feature has already run, just log the error
        print(f"[SUBSCRIPTIONS] record usage error feature={feature}: {e}", flush=True)


async def get_usage_state(user_id: int) -> dict:
    """
    Returns the full usage state for a user — called by /auth/me.

    Returns:
    {
        "tier": "free",
        "tier_label": "Free",
        "next_tier": "basic",
        "next_tier_price": 15,
        "features": {
            "chart_analysis": {
                "label": "Chart Analysis",
                "used": 1,
                "limit": 2,
                "remaining": 1,
                "resets": null,
                "unlimited": false
            },
            ...
        }
    }
    """
    tier = await _get_user_tier(user_id)
    tier_info = TIER_INFO.get(tier, TIER_INFO["free"])
    next_tier = tier_info.get("next")

    features = {}
    for feature, cfg in FEATURE_CONFIG.items():
        tier_cfg = cfg.get(tier) or cfg.get("free")
        limit = await _get_limit(tier_cfg["limit_key"], tier_cfg["default"])
        reset = tier_cfg["reset"]
        unlimited = limit >= 999

        if unlimited:
            used = await _count_usage(user_id, cfg["table"], reset)
            remaining = 999
        else:
            used = await _count_usage(user_id, cfg["table"], reset)
            remaining = max(0, limit - used)

        features[feature] = {
            "label":     cfg["label"],
            "used":      used,
            "limit":     limit,
            "remaining": remaining,
            "resets":    _reset_label(reset),
            "unlimited": unlimited,
            "at_limit":  not unlimited and remaining <= 0,
            "warning":   not unlimited and 0 < remaining <= 1,
        }

    return {
        "tier":            tier,
        "tier_label":      tier_info["name"],
        "next_tier":       next_tier,
        "next_tier_price": TIER_INFO.get(next_tier, {}).get("price") if next_tier else None,
        "features":        features,
    }
