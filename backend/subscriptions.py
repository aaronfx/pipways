from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .database import database

# ══════════════════════════════════════════════════════════════════════════════
# TABLE BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════

async def init_subscription_tables():
    """
    Create all AI usage log tables idempotently.
    Called from main.py lifespan AND auto_setup.py (which previously failed
    because this function didn't exist).
    """
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
    await database.execute(
        "CREATE INDEX IF NOT EXISTS idx_cal_user_date "
        "ON chart_analysis_logs (user_id, created_at DESC)"
    )
    await database.execute("""
        CREATE TABLE IF NOT EXISTS ai_mentor_logs (
            id             SERIAL PRIMARY KEY,
            user_id        INTEGER NOT NULL,
            question_topic VARCHAR(100),
            created_at     TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await database.execute(
        "CREATE INDEX IF NOT EXISTS idx_aml_user_date "
        "ON ai_mentor_logs (user_id, created_at DESC)"
    )
    await database.execute("""
        CREATE TABLE IF NOT EXISTS journal_uploads (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            filename   VARCHAR(255),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await database.execute(
        "CREATE INDEX IF NOT EXISTS idx_ju_user_date "
        "ON journal_uploads (user_id, created_at DESC)"
    )
    await database.execute("""
        CREATE TABLE IF NOT EXISTS stock_analysis_logs (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            symbol     VARCHAR(20),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
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

    async def _count(sql, params):
        try:
            row = await database.fetch_one(sql, params)
            return int(row["cnt"]) if row else 0
        except Exception:
            return 0

    return {
        "chart_analysis": await _count(
            "SELECT COUNT(*) AS cnt FROM chart_analysis_logs "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": today}
        ),
        "ai_mentor": await _count(
            "SELECT COUNT(*) AS cnt FROM ai_mentor_logs "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": today}
        ),
        "performance_analysis": await _count(
            "SELECT COUNT(*) AS cnt FROM journal_uploads "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": month_start}
        ),
        "stock_research": await _count(
            "SELECT COUNT(*) AS cnt FROM stock_analysis_logs "
            "WHERE user_id = :uid AND created_at >= :start",
            {"uid": user_id, "start": today}
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# GENERIC LIMIT CHECK & LOG  (used by all 4 service endpoints)
# ══════════════════════════════════════════════════════════════════════════════

_LIMIT_MAP = {
    # feature_key              log_table                free  pro
    "chart_analysis":        ("chart_analysis_logs",    2,    50),
    "ai_mentor":             ("ai_mentor_logs",         5,    200),
    "performance_analysis":  ("journal_uploads",        1,    None),   # monthly
    "stock_research":        ("stock_analysis_logs",    3,    100),
}

_MONTHLY_FEATURES = {"performance_analysis"}


async def check_limit(user_id: int, user_tier: str, feature: str) -> bool:
    """
    Returns True if the user is under their usage limit.
    Fails open on DB error so a table hiccup never blocks users.
    """
    if feature not in _LIMIT_MAP:
        return True

    table, free_limit, pro_limit = _LIMIT_MAP[feature]
    limit = pro_limit if user_tier == "pro" else free_limit

    if limit is None:
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
        return used < limit
    except Exception as e:
        print(f"[check_limit] {feature}: {e}", flush=True)
        return True  # fail open


async def log_usage(user_id: int, feature: str, **kwargs):
    """
    Insert one row into the feature's log table after a SUCCESSFUL response.
    Extra kwargs forwarded as columns (symbol, timeframe, question_topic, filename).
    Non-fatal on any error.
    """
    if feature not in _LIMIT_MAP:
        return

    table = _LIMIT_MAP[feature][0]

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
