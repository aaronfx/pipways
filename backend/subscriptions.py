from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, Dict, Any
import json
from datetime import datetime, timedelta

from .database import database          # databases library instance (not get_database)
from .models import User, SiteSetting

# Enhanced feature configuration including signals
FEATURE_CONFIG = {
    "chart_analysis_daily": {
        "free": 2,
        "pro": 50
    },
    "ai_mentor_daily": {
        "free": 5,
        "pro": 200
    },
    "performance_analysis_monthly": {
        "free": 1,
        "pro": None  # Unlimited
    },
    "stock_research_daily": {
        "free": 3,
        "pro": 100
    },
    # Enhanced signals features
    "signals_visible": {
        "free": 3,      # Free users see 3 signals
        "pro": None     # Pro users see all signals
    },
    "signals_detailed_analysis": {
        "free": 1,      # Free users get 1 detailed analysis per day
        "pro": None     # Pro users get unlimited
    },
    "signals_chart_access": {
        "free": False,  # Free users can't access full charts
        "pro": True     # Pro users get full chart access
    },
    "signals_pattern_filtering": {
        "free": False,  # Free users can't filter by pattern
        "pro": True     # Pro users get advanced filtering
    },
    "signals_email_alerts": {
        "free": False,  # Free users don't get email alerts
        "pro": True     # Pro users get email alerts
    },
    "webinar_recordings": {
        "free": False,
        "pro": True
    }
}

async def get_feature_limit(db: AsyncSession, feature: str, tier: str) -> Optional[int]:
    """Get feature limit from database or fallback to default config"""
    try:
        # Try to get from database first
        query = select(SiteSetting).where(SiteSetting.key == f"{feature}_{tier}")
        result = await db.execute(query)
        setting = result.scalar_one_or_none()
        
        if setting and setting.value:
            try:
                return int(setting.value) if setting.value.lower() != 'none' else None
            except (ValueError, AttributeError):
                pass
        
        # Fallback to default config
        return FEATURE_CONFIG.get(feature, {}).get(tier)
        
    except Exception as e:
        print(f"Error getting feature limit for {feature}_{tier}: {e}")
        return FEATURE_CONFIG.get(feature, {}).get(tier)

async def get_feature_access(db: AsyncSession, feature: str, tier: str) -> bool:
    """Check if user tier has access to a boolean feature"""
    try:
        limit = await get_feature_limit(db, feature, tier)
        if limit is None:
            return True  # Unlimited access
        elif isinstance(limit, bool):
            return limit
        elif isinstance(limit, int):
            return limit > 0
        else:
            return False
    except Exception as e:
        print(f"Error checking feature access for {feature}_{tier}: {e}")
        return False

async def check_feature_access(db: AsyncSession, user_id: int, feature: str, usage_amount: int = 1) -> bool:
    """Check if user can access a feature and has remaining usage"""
    try:
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False
        
        tier = user.subscription_tier or "free"
        
        # Get feature limit
        limit = await get_feature_limit(db, feature, tier)
        
        # Handle unlimited access
        if limit is None:
            return True
        
        # Handle boolean features
        if isinstance(limit, bool):
            return limit
        
        # Handle numeric limits - check current usage
        if isinstance(limit, int):
            current_usage = await get_current_usage(db, user_id, feature)
            return (current_usage + usage_amount) <= limit
        
        return False
        
    except Exception as e:
        print(f"Error checking feature access: {e}")
        return False

async def get_current_usage(db: AsyncSession, user_id: int, feature: str) -> int:
    """Get current usage count for a feature"""
    try:
        # Determine the time period for the feature
        if "_daily" in feature:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        elif "_monthly" in feature:
            start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # For signals and other features, use daily period
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Map features to their respective log tables
        usage_queries = {
            "chart_analysis_daily": "SELECT COUNT(*) FROM chart_analysis_logs WHERE user_id = :user_id AND created_at >= :start_date",
            "ai_mentor_daily": "SELECT COUNT(*) FROM ai_mentor_logs WHERE user_id = :user_id AND created_at >= :start_date",
            "performance_analysis_monthly": "SELECT COUNT(*) FROM journal_uploads WHERE user_id = :user_id AND created_at >= :start_date",
            "stock_research_daily": "SELECT COUNT(*) FROM stock_analysis_logs WHERE user_id = :user_id AND created_at >= :start_date",
            "signals_detailed_analysis": "SELECT COUNT(*) FROM chart_analysis_logs WHERE user_id = :user_id AND analysis_type = 'signal_detailed' AND created_at >= :start_date"
        }
        
        query_sql = usage_queries.get(feature)
        if not query_sql:
            return 0
        
        from sqlalchemy import text
        result = await db.execute(text(query_sql), {"user_id": user_id, "start_date": start_date})
        count = result.scalar() or 0
        return int(count)
        
    except Exception as e:
        print(f"Error getting current usage for {feature}: {e}")
        return 0

async def log_feature_usage(db: AsyncSession, user_id: int, feature: str, metadata: Optional[Dict[Any, Any]] = None):
    """Log feature usage for tracking"""
    try:
        # For signals detailed analysis, log to chart_analysis_logs
        if feature == "signals_detailed_analysis":
            from .models import ChartAnalysisLog
            log_entry = ChartAnalysisLog(
                user_id=user_id,
                analysis_type="signal_detailed",
                symbol=metadata.get("symbol", "") if metadata else "",
                timeframe=metadata.get("timeframe", "") if metadata else "",
                metadata=metadata
            )
            db.add(log_entry)
            await db.commit()
        
        # Add logging for other signal features as needed
        
    except Exception as e:
        print(f"Error logging feature usage: {e}")

async def get_user_limits_summary(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Get comprehensive summary of user's feature limits and current usage"""
    try:
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return {}
        
        tier = user.subscription_tier or "free"
        summary = {
            "tier": tier,
            "features": {}
        }
        
        # Get limits and usage for all features
        for feature in FEATURE_CONFIG.keys():
            limit = await get_feature_limit(db, feature, tier)
            
            if isinstance(limit, bool):
                summary["features"][feature] = {
                    "limit": limit,
                    "usage": None,
                    "remaining": None,
                    "has_access": limit
                }
            elif isinstance(limit, int):
                current_usage = await get_current_usage(db, user_id, feature)
                summary["features"][feature] = {
                    "limit": limit,
                    "usage": current_usage,
                    "remaining": max(0, limit - current_usage),
                    "has_access": current_usage < limit
                }
            elif limit is None:
                summary["features"][feature] = {
                    "limit": "unlimited",
                    "usage": None,
                    "remaining": "unlimited",
                    "has_access": True
                }
            else:
                summary["features"][feature] = {
                    "limit": limit,
                    "usage": None,
                    "remaining": None,
                    "has_access": False
                }
        
        return summary
        
    except Exception as e:
        print(f"Error getting user limits summary: {e}")
        return {}

async def update_feature_limit(db: AsyncSession, feature: str, tier: str, limit: Any):
    """Update feature limit in database"""
    try:
        key = f"{feature}_{tier}"
        
        # Convert limit to string for storage
        if limit is None:
            value = "none"
        elif isinstance(limit, bool):
            value = "true" if limit else "false"
        else:
            value = str(limit)
        
        # Check if setting exists
        query = select(SiteSetting).where(SiteSetting.key == key)
        result = await db.execute(query)
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = SiteSetting(
                key=key,
                value=value,
                description=f"Feature limit for {feature} on {tier} tier"
            )
            db.add(setting)
        
        await db.commit()
        return True
        
    except Exception as e:
        print(f"Error updating feature limit: {e}")
        return False

# Enhanced signals-specific functions

async def can_view_signals(db: AsyncSession, user_id: int, requested_count: int = 1) -> bool:
    """Check if user can view signals"""
    return await check_feature_access(db, user_id, "signals_visible", requested_count)

async def can_access_detailed_analysis(db: AsyncSession, user_id: int) -> bool:
    """Check if user can access detailed signal analysis"""
    return await check_feature_access(db, user_id, "signals_detailed_analysis", 1)

async def can_access_full_charts(db: AsyncSession, user_id: int) -> bool:
    """Check if user can access full chart functionality"""
    user_query = select(User).where(User.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return False
    
    tier = user.subscription_tier or "free"
    return await get_feature_access(db, "signals_chart_access", tier)

async def can_use_advanced_filters(db: AsyncSession, user_id: int) -> bool:
    """Check if user can use advanced pattern filtering"""
    user_query = select(User).where(User.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return False
    
    tier = user.subscription_tier or "free"
    return await get_feature_access(db, "signals_pattern_filtering", tier)

async def can_receive_signal_alerts(db: AsyncSession, user_id: int) -> bool:
    """Check if user can receive signal email alerts"""
    user_query = select(User).where(User.id == user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return False
    
    tier = user.subscription_tier or "free"
    return await get_feature_access(db, "signals_email_alerts", tier)

# Helper function for 402 error responses
def create_upgrade_required_response(feature: str, current_tier: str = "free"):
    """Create standardized 402 response for upgrade requirements"""
    
    feature_messages = {
        "signals_detailed_analysis": {
            "title": "Detailed Signal Analysis",
            "message": "Upgrade to Pro to access in-depth chart analysis and pattern insights.",
            "features": ["Unlimited detailed analysis", "AI pattern recognition", "Risk/reward calculations"]
        },
        "signals_chart_access": {
            "title": "Full Chart Access",
            "message": "Upgrade to Pro to access interactive charts and TradingView integration.",
            "features": ["Interactive charts", "Technical indicators", "Pattern overlays"]
        },
        "signals_pattern_filtering": {
            "title": "Advanced Filtering",
            "message": "Upgrade to Pro to filter signals by pattern, confidence, and asset type.",
            "features": ["Pattern-based filtering", "Confidence levels", "Multi-asset filtering"]
        },
        "signals_email_alerts": {
            "title": "Signal Alerts",
            "message": "Upgrade to Pro to receive instant email alerts for new trading signals.",
            "features": ["Real-time email alerts", "Custom notification settings", "Priority signals"]
        }
    }
    
    default_message = {
        "title": "Premium Feature",
        "message": "Upgrade to Pro to access this advanced trading feature.",
        "features": ["Enhanced functionality", "Priority support", "Advanced tools"]
    }
    
    return feature_messages.get(feature, default_message)


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
