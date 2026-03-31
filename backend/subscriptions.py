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

    async def _count(table: str, sql: str, params: dict) -> int:
        """
        Run a COUNT query and return the result.
        Logs failures explicitly — was previously silently returning 0 on any
        error (table missing, bad params, connection issue), which caused the
        usage badge to always show the full free limit regardless of actual use.
        """
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

_LIMIT_MAP = {
    # feature_key              log_table                free  basic  pro
    "chart_analysis":        ("chart_analysis_logs",    2,    50,    None),
    "ai_mentor":             ("ai_mentor_logs",         5,    200,   None),
    "performance_analysis":  ("journal_uploads",        1,    10,    None),  # monthly
    "stock_research":        ("stock_analysis_logs",    3,    100,   None),
}

_MONTHLY_FEATURES = {"performance_analysis"}


async def check_limit(user_id: int, user_tier: str, feature: str) -> bool:
    """
    Returns True if the user is under their usage limit.
    Supports free / basic / pro tiers.
    Fails open on DB error so a hiccup never blocks users.
    """
    if feature not in _LIMIT_MAP:
        return True

    table, free_limit, basic_limit, pro_limit = _LIMIT_MAP[feature]

    if user_tier == "pro":
        limit = pro_limit
    elif user_tier == "basic":
        limit = basic_limit
    else:
        limit = free_limit

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

    Self-heals: if the table is missing (init_subscription_tables() was never
    called from main.py lifespan), it creates the tables automatically and
    retries once — so usage logging works correctly from the very first deploy.
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
    sql = (
        f"INSERT INTO {table} ({col_names}, created_at) "
        f"VALUES ({col_values}, NOW())"
    )

    try:
        await database.execute(sql, cols)
        print(f"[log_usage] ✅ {feature} logged for user={user_id}", flush=True)
    except Exception as e:
        err = str(e).lower()
        # Table does not exist — auto-create all tables and retry once
        if "does not exist" in err or "no such table" in err or "undefined table" in err:
            print(
                f"[log_usage] Table '{table}' missing — running init_subscription_tables() "
                f"and retrying for {feature}",
                flush=True,
            )
            try:
                await init_subscription_tables()
                await database.execute(sql, cols)
                print(f"[log_usage] ✅ {feature} logged after self-heal for user={user_id}", flush=True)
            except Exception as retry_e:
                print(f"[log_usage] ❌ Retry failed for {feature} user={user_id}: {retry_e}", flush=True)
        else:
            print(f"[log_usage] ❌ {feature} failed for user={user_id}: {e}", flush=True)


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
