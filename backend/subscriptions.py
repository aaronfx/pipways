from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .database import database

# ══════════════════════════════════════════════════════════════════════════════
# TABLE BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════

async def init_subscription_tables():
    """
    Create all AI usage log tables idempotently AND add any missing columns
    to existing tables. CREATE TABLE IF NOT EXISTS never touches existing tables,
    so columns added in later deploys would never appear — causing the
    'column X does not exist' INSERT failures seen in production logs.
    """
    # ── chart_analysis_logs ───────────────────────────────────────────────────
    await database.execute("""
        CREATE TABLE IF NOT EXISTS chart_analysis_logs (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL,
            analysis_type VARCHAR(50) DEFAULT 'chart_analysis',
            symbol        VARCHAR(20),
            timeframe     VARCHAR(10),
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    # Ensure columns exist in case table was created by an older deploy
    for col_def in [
        "analysis_type VARCHAR(50) DEFAULT 'chart_analysis'",
        "symbol        VARCHAR(20)",
        "timeframe     VARCHAR(10)",
    ]:
        col_name = col_def.split()[0]
        await database.execute(
            f"ALTER TABLE chart_analysis_logs ADD COLUMN IF NOT EXISTS {col_def};"
        )
    await database.execute(
        "CREATE INDEX IF NOT EXISTS idx_cal_user_date "
        "ON chart_analysis_logs (user_id, created_at DESC)"
    )

    # ── ai_mentor_logs ────────────────────────────────────────────────────────
    await database.execute("""
        CREATE TABLE IF NOT EXISTS ai_mentor_logs (
            id             SERIAL PRIMARY KEY,
            user_id        INTEGER NOT NULL,
            question_topic VARCHAR(100),
            created_at     TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await database.execute(
        "ALTER TABLE ai_mentor_logs ADD COLUMN IF NOT EXISTS question_topic VARCHAR(100);"
    )
    await database.execute(
        "CREATE INDEX IF NOT EXISTS idx_aml_user_date "
        "ON ai_mentor_logs (user_id, created_at DESC)"
    )

    # ── journal_uploads ───────────────────────────────────────────────────────
    await database.execute("""
        CREATE TABLE IF NOT EXISTS journal_uploads (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            filename   VARCHAR(255),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await database.execute(
        "ALTER TABLE journal_uploads ADD COLUMN IF NOT EXISTS filename VARCHAR(255);"
    )
    await database.execute(
        "CREATE INDEX IF NOT EXISTS idx_ju_user_date "
        "ON journal_uploads (user_id, created_at DESC)"
    )

    # ── stock_analysis_logs ───────────────────────────────────────────────────
    await database.execute("""
        CREATE TABLE IF NOT EXISTS stock_analysis_logs (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            symbol     VARCHAR(20),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await database.execute(
        "ALTER TABLE stock_analysis_logs ADD COLUMN IF NOT EXISTS symbol VARCHAR(20);"
    )
    await database.execute(
        "CREATE INDEX IF NOT EXISTS idx_sal_user_date "
        "ON stock_analysis_logs (user_id, created_at DESC)"
    )

    print("[subscriptions] ✅ All usage log tables ready", flush=True)


# Alias so any old caller still works
ensure_chart_analysis_logs_table = init_subscription_tables


# ══════════════════════════════════════════════════════════════════════════════
# USAGE STATE  (called by /auth/me)
# ══════════════════════════════════════════════════════════════════════════════

async def get_usage_state(user_id: int) -> Dict[str, int]:
    """
    Returns today's (or this month's) usage counts keyed by short feature name.
    Keys must match usage.js FEATURE_CONFIG exactly:
        chart_analysis, ai_mentor, performance_analysis, stock_research
    """
    today       = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async def _count(table: str, sql: str, params: dict) -> int:
        try:
            row = await database.fetch_one(sql, params)
            count = int(row["cnt"]) if row else 0
            print(f"[usage] {table} user={user_id} count={count}", flush=True)
            return count
        except Exception as exc:
            print(f"[usage] ⚠️  {table} query failed for user={user_id}: {exc}", flush=True)
            return 0

    return {
        "chart_analysis": await _count(
            "chart_analysis_logs",
            "SELECT COUNT(*) AS cnt FROM chart_analysis_logs "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": today}
        ),
        "ai_mentor": await _count(
            "ai_mentor_logs",
            "SELECT COUNT(*) AS cnt FROM ai_mentor_logs "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": today}
        ),
        "performance_analysis": await _count(
            "journal_uploads",
            "SELECT COUNT(*) AS cnt FROM journal_uploads "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": month_start}
        ),
        "stock_research": await _count(
            "stock_analysis_logs",
            "SELECT COUNT(*) AS cnt FROM stock_analysis_logs "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": today}
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# GENERIC LIMIT CHECK & LOG  (used by all 4 service endpoints)
# ══════════════════════════════════════════════════════════════════════════════

# ── CMS key mapping ──────────────────────────────────────────────────────────
# Maps feature keys to (log_table, free_cms_key, pro_cms_key, default_free, default_pro)
_FEATURE_CONFIG = {
    "chart_analysis":       ("chart_analysis_logs",  "chart_free_daily",    "chart_pro_daily",    2,   50),
    "ai_mentor":            ("ai_mentor_logs",       "mentor_free_daily",   "mentor_pro_daily",   5,   200),
    "performance_analysis": ("journal_uploads",      "journal_free_imports","journal_pro_imports", 1,   10),
    "stock_research":       ("stock_analysis_logs",  "stock_free_daily",    "stock_pro_daily",    3,   100),
}

# Cache for CMS limits — refreshed periodically
_cms_limits_cache = {}
_cms_cache_ts = 0
_CMS_CACHE_TTL = 300  # 5 minutes


async def _load_cms_limits():
    """Load feature limits from site_settings table. Returns dict of key→value."""
    global _cms_limits_cache, _cms_cache_ts
    import time
    now = time.monotonic()
    if _cms_limits_cache and (now - _cms_cache_ts) < _CMS_CACHE_TTL:
        return _cms_limits_cache

    try:
        rows = await database.fetch_all(
            "SELECT key, value FROM site_settings WHERE key LIKE :pattern",
            {"pattern": "%_daily"}
        )
        rows2 = await database.fetch_all(
            "SELECT key, value FROM site_settings WHERE key LIKE :pattern",
            {"pattern": "%_imports"}
        )
        result = {}
        for row in list(rows) + list(rows2):
            k = row["key"] if isinstance(row, dict) else getattr(row, "key", None)
            v = row["value"] if isinstance(row, dict) else getattr(row, "value", None)
            if k and v:
                try:
                    result[k] = int(v)
                except (ValueError, TypeError):
                    pass
        _cms_limits_cache = result
        _cms_cache_ts = now
        return result
    except Exception as e:
        print(f"[subscriptions] CMS limits load error: {e}", flush=True)
        return _cms_limits_cache  # return stale cache on error


_MONTHLY_FEATURES = {"performance_analysis"}

# Legacy hardcoded limits (kept for reference; check_limit() now reads from CMS site_settings)
_LIMIT_MAP = {
    # feature_key              log_table                free  basic  pro
    "chart_analysis":        ("chart_analysis_logs",    2,    50,    None),
    "ai_mentor":             ("ai_mentor_logs",         5,    200,   None),
    "performance_analysis":  ("journal_uploads",        1,    10,    None),  # monthly
    "stock_research":        ("stock_analysis_logs",    3,    100,   None),
}


async def check_limit(user_id: int, user_tier: str, feature: str) -> bool:
    """
    Returns True if the user is under their usage limit.
    Reads limits from CMS site_settings with hardcoded fallbacks.
    Fails open on DB error so a hiccup never blocks users.
    """
    if feature not in _FEATURE_CONFIG:
        return True

    table, free_key, pro_key, default_free, default_pro = _FEATURE_CONFIG[feature]

    # Pro tier = unlimited by default
    if user_tier in ("pro", "pro_plus"):
        # Check if CMS set a pro limit
        cms = await _load_cms_limits()
        pro_val = cms.get(pro_key)
        if pro_val is None or pro_val == 0:
            return True  # unlimited
        limit = pro_val
    elif user_tier == "basic":
        cms = await _load_cms_limits()
        limit = cms.get(pro_key, default_pro)  # basic gets pro limits
    else:
        cms = await _load_cms_limits()
        limit = cms.get(free_key, default_free)

    if limit is None or limit == 0:
        return True  # unlimited

    is_monthly = feature in _MONTHLY_FEATURES
    start = (
        datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if is_monthly else
        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    )

    try:
        row = await database.fetch_one(
            f"SELECT COUNT(*) AS cnt FROM {table} "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": start}
        )
        used = int(row["cnt"]) if row else 0
        allowed = used < limit
        print(
            f"[check_limit] {feature} user={user_id} tier={user_tier} "
            f"used={used} limit={limit} (cms={free_key if user_tier=='free' else pro_key}) "
            f"period={'monthly' if is_monthly else 'daily'} "
            f"→ {'ALLOW' if allowed else 'BLOCK'}",
            flush=True
        )
        return allowed
    except Exception as e:
        print(f"[check_limit] {feature} user={user_id}: error — {e} (fail open)", flush=True)
        return True  # fail open


async def log_usage(user_id: int, feature: str, **kwargs):
    """
    Insert one row into the feature's log table after a SUCCESSFUL response.
    Extra kwargs forwarded as columns (symbol, timeframe, question_topic, filename).
    Non-fatal on any error.
    """
    if feature not in _FEATURE_CONFIG:
        return

    table = _FEATURE_CONFIG[feature][0]

    _allowed_cols = {
        "chart_analysis_logs":  {"symbol", "timeframe", "analysis_type"},
        "ai_mentor_logs":       {"question_topic"},
        "journal_uploads":      {"filename"},
        "stock_analysis_logs":  {"symbol"},
    }

    cols: Dict[str, Any] = {"user_id": user_id}
    for k, v in kwargs.items():
        if k in _allowed_cols.get(table, set()):
            cols[k] = str(v)[:255] if v else ""

    col_names  = ", ".join(cols.keys())
    col_values = ", ".join(f":{k}" for k in cols.keys())

    try:
        await database.execute(
            f"INSERT INTO {table} ({col_names}, created_at) "
            f"VALUES ({col_values}, NOW())",
            cols
        )
    except Exception as e:
        print(f"[log_usage] {feature}: {e}", flush=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE WRAPPERS (keep old callers working)
# ══════════════════════════════════════════════════════════════════════════════

async def check_chart_analysis_limit(user_id: int, user_tier: str) -> bool:
    return await check_limit(user_id, user_tier, "chart_analysis")

async def log_chart_analysis(user_id: int, symbol: str = "", timeframe: str = ""):
    await log_usage(user_id, "chart_analysis", symbol=symbol, timeframe=timeframe)

async def check_ai_mentor_limit(user_id: int, user_tier: str) -> bool:
    return await check_limit(user_id, user_tier, "ai_mentor")

async def log_ai_mentor(user_id: int, question_topic: str = ""):
    await log_usage(user_id, "ai_mentor", question_topic=question_topic)

async def check_performance_limit(user_id: int, user_tier: str) -> bool:
    return await check_limit(user_id, user_tier, "performance_analysis")

async def log_performance_analysis(user_id: int, filename: str = ""):
    await log_usage(user_id, "performance_analysis", filename=filename)

async def check_stock_research_limit(user_id: int, user_tier: str) -> bool:
    return await check_limit(user_id, user_tier, "stock_research")

async def log_stock_research(user_id: int, symbol: str = ""):
    await log_usage(user_id, "stock_research", symbol=symbol)
