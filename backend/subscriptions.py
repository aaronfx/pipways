"""
Pipways Subscription & Usage Enforcement — v2.0

KEY FIX: All site_settings keys now match exactly what cms.js saves.
cms.js uses:  chart_free_daily, chart_pro_daily,
              mentor_free_daily, mentor_pro_daily,
              stock_free_daily, stock_pro_daily,
              journal_free_imports, journal_pro_imports,
              signals_free_limit, signals_pro_limit

This file reads the SAME keys so admin panel changes take effect immediately.

Provides:
  • check_and_record_usage()  — gating function for every feature route
  • get_usage_state()         — called by /auth/me
  • init_subscription_tables()— creates tables on startup
"""

from fastapi import HTTPException
from datetime import datetime, date
from typing import Optional
from .database import database


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE CONFIGURATION
# Keys MUST match exactly what cms.js writes to site_settings.
# ═══════════════════════════════════════════════════════════════════════════════

FEATURE_CONFIG = {
    "chart_analysis": {
        "label": "Chart Analysis",
        "free": {"limit_key": "chart_free_daily",  "reset": "daily", "default": 2},
        "pro":  {"limit_key": "chart_pro_daily",   "reset": "daily", "default": 50},
        "table": "chart_analysis_logs",
    },
    "performance": {
        "label": "Performance Analysis",
        "free": {"limit_key": "journal_free_imports", "reset": "monthly", "default": 1},
        "pro":  {"limit_key": "journal_pro_imports",  "reset": "monthly", "default": 999},
        "table": "journal_uploads",
    },
    "ai_mentor": {
        "label": "AI Mentor",
        "free": {"limit_key": "mentor_free_daily", "reset": "daily", "default": 5},
        "pro":  {"limit_key": "mentor_pro_daily",  "reset": "daily", "default": 200},
        "table": "ai_mentor_logs",
    },
    "stock_research": {
        "label": "AI Stock Research",
        "free": {"limit_key": "stock_free_daily", "reset": "daily", "default": 3},
        "pro":  {"limit_key": "stock_pro_daily",  "reset": "daily", "default": 100},
        "table": "stock_analysis_logs",
    },
}

# Seeded into site_settings on first startup.
# Keys match cms.js Feature Limits panel exactly.
# ON CONFLICT DO NOTHING — admin edits are never overwritten.
_DEFAULT_LIMIT_SETTINGS = {
    # Chart Analysis
    "chart_free_daily":      "2",
    "chart_pro_daily":       "50",
    # Performance / Journal
    "journal_free_imports":  "1",
    "journal_pro_imports":   "999",
    # AI Mentor
    "mentor_free_daily":     "5",
    "mentor_pro_daily":      "200",
    # AI Stock Research
    "stock_free_daily":      "3",
    "stock_pro_daily":       "100",
    # Signals (read by signals.py)
    "signals_free_limit":    "3",
    "signals_pro_limit":     "999",
    # Misc CMS settings
    "blog_free_limit":       "10",
    "webinar_free_limit":    "1",
    "webinar_pro_limit":     "999",
    "courses_free_access":   "2",
}

# Tier info for upgrade modal responses
TIER_INFO = {
    "free": {"name": "Free",  "price_ngn": None,   "next": "pro"},
    "pro":  {"name": "Pro",   "price_ngn": 15000,  "next": None},
}


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE INIT
# ═══════════════════════════════════════════════════════════════════════════════

async def init_subscription_tables():
    """
    Creates usage log tables and seeds default limits.
    Idempotent — safe to call on every startup.
    """
    tables = [
        """CREATE TABLE IF NOT EXISTS stock_analysis_logs (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
            ticker     VARCHAR(50) NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS chart_analysis_logs (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
            symbol     VARCHAR(20) DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS ai_mentor_logs (
            id             SERIAL PRIMARY KEY,
            user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
            question_topic VARCHAR(255) DEFAULT '',
            created_at     TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS journal_uploads (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS site_settings (
            key        VARCHAR(120) PRIMARY KEY,
            value      TEXT NOT NULL DEFAULT '',
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
    ]

    column_patches = [
        "ALTER TABLE chart_analysis_logs ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE ai_mentor_logs      ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE journal_uploads     ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
    ]

    for sql in tables + column_patches:
        try:
            await database.execute(sql)
        except Exception as e:
            print(f"[SUBSCRIPTIONS] table init warning: {e}", flush=True)

    # Seed default limits — never overwrites admin edits
    seeded = 0
    for key, value in _DEFAULT_LIMIT_SETTINGS.items():
        try:
            await database.execute(
                """INSERT INTO site_settings (key, value, updated_at)
                   VALUES (:k, :v, NOW())
                   ON CONFLICT (key) DO NOTHING""",
                {"k": key, "v": value},
            )
            seeded += 1
        except Exception as e:
            print(f"[SUBSCRIPTIONS] settings seed warning: {e}", flush=True)

    print(f"[SUBSCRIPTIONS] Tables and settings ready. {seeded} defaults seeded.", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def _get_user_tier(user_id: int) -> str:
    try:
        row = await database.fetch_one(
            "SELECT subscription_tier FROM users WHERE id = :uid",
            {"uid": user_id},
        )
        if row:
            tier = row["subscription_tier"] or "free"
            # Normalise legacy values to two-tier model
            if tier in ("enterprise", "basic"):
                return "pro"
            return tier
        return "free"
    except Exception as e:
        print(f"[SUBSCRIPTIONS] get tier error user={user_id}: {e}", flush=True)
        return "free"


async def _get_limit(limit_key: str, default: int) -> int:
    """Read limit from site_settings, fall back to hardcoded default."""
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
    base = f"SELECT COUNT(*) AS c FROM {table} WHERE user_id = :uid"
    if reset == "lifetime":
        return base
    if reset == "daily":
        return base + " AND created_at >= CURRENT_DATE"
    if reset == "monthly":
        return base + " AND created_at >= DATE_TRUNC('month', NOW())"
    return base


async def _count_usage(user_id: int, table: str, reset: str) -> int:
    try:
        query = _count_query(table, reset)
        row = await database.fetch_one(query, {"uid": user_id})
        return int(row["c"]) if row else 0
    except Exception as e:
        print(f"[SUBSCRIPTIONS] count error table={table}: {e}", flush=True)
        return 0


def _reset_label(reset: str) -> Optional[str]:
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
    Main gate function. Call at the top of every gated route.
    Raises HTTP 402 if limit reached.
    Returns usage dict on success: {used, limit, remaining, tier}
    """
    cfg = FEATURE_CONFIG.get(feature)
    if not cfg:
        return {"used": 0, "limit": 999, "remaining": 999, "tier": "free"}

    tier = await _get_user_tier(user_id)
    tier_cfg = cfg.get(tier) or cfg.get("free")
    limit = await _get_limit(tier_cfg["limit_key"], tier_cfg["default"])
    reset = tier_cfg["reset"]
    used  = await _count_usage(user_id, cfg["table"], reset)

    if limit < 999 and used >= limit:
        tier_info = TIER_INFO.get(tier, {})
        next_tier = tier_info.get("next")
        raise HTTPException(
            status_code=402,
            detail={
                "error":                 "limit_reached",
                "feature":               feature,
                "feature_label":         cfg["label"],
                "used":                  used,
                "limit":                 limit,
                "tier":                  tier,
                "next_tier":             next_tier,
                "next_tier_price_ngn":   TIER_INFO.get(next_tier, {}).get("price_ngn") if next_tier else None,
                "resets":                _reset_label(reset),
                "upgrade_url":           "/pricing.html",
            },
        )

    await _record_usage(user_id, feature, cfg["table"], metadata or {})

    remaining = max(0, limit - used - 1) if limit < 999 else 999
    return {
        "used":      used + 1,
        "limit":     limit,
        "remaining": remaining,
        "tier":      tier,
    }


async def _record_usage(user_id: int, feature: str, table: str, metadata: dict) -> None:
    """Insert a usage event into the feature's log table."""
    try:
        if table == "chart_analysis_logs":
            await database.execute(
                "INSERT INTO chart_analysis_logs (user_id, created_at) VALUES (:uid, NOW())",
                {"uid": user_id},
            )
        elif table == "ai_mentor_logs":
            await database.execute(
                "INSERT INTO ai_mentor_logs (user_id, created_at, question_topic) VALUES (:uid, NOW(), :topic)",
                {"uid": user_id, "topic": metadata.get("topic", "")},
            )
        elif table == "journal_uploads":
            await database.execute(
                "INSERT INTO journal_uploads (user_id, created_at) VALUES (:uid, NOW())",
                {"uid": user_id},
            )
        elif table == "stock_analysis_logs":
            await database.execute(
                "INSERT INTO stock_analysis_logs (user_id, ticker, created_at) VALUES (:uid, :ticker, NOW())",
                {"uid": user_id, "ticker": metadata.get("ticker", "")},
            )
    except Exception as e:
        print(f"[SUBSCRIPTIONS] record usage error feature={feature}: {e}", flush=True)


async def get_usage_state(user_id: int) -> dict:
    """Full usage state for /auth/me response."""
    tier = await _get_user_tier(user_id)
    tier_info = TIER_INFO.get(tier, TIER_INFO["free"])
    next_tier = tier_info.get("next")

    features = {}
    for feature, cfg in FEATURE_CONFIG.items():
        tier_cfg = cfg.get(tier) or cfg.get("free")
        limit    = await _get_limit(tier_cfg["limit_key"], tier_cfg["default"])
        reset    = tier_cfg["reset"]
        unlimited = limit >= 999
        used     = await _count_usage(user_id, cfg["table"], reset)
        remaining = 999 if unlimited else max(0, limit - used)

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
        "tier":                tier,
        "tier_label":          tier_info["name"],
        "next_tier":           next_tier,
        "next_tier_price_ngn": TIER_INFO.get(next_tier, {}).get("price_ngn") if next_tier else None,
        "features":            features,
    }
