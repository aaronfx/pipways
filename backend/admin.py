"""
Admin panel API — Production Grade
Fixes: complete stats payload, is_superuser check, user management,
       trading analytics, and AI usage endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date, timedelta

from .security import get_current_user
from .database import database, users

router = APIRouter()


# ── Admin guard ────────────────────────────────────────────────────────────────

async def get_admin_user(current_user=Depends(get_current_user)):
    """
    Verify the caller is an administrator.
    Accepts any of: is_admin=True, role='admin', is_superuser=True.
    """
    def _is_admin(u) -> bool:
        if isinstance(u, dict):
            return (
                u.get("is_admin") is True
                or u.get("role") == "admin"
                or u.get("is_superuser") is True
            )
        return (
            getattr(u, "is_admin", False) is True
            or getattr(u, "role", None) == "admin"
            or getattr(u, "is_superuser", False) is True
        )

    if not _is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _safe_count(query: str, values: dict | None = None) -> int:
    """Run a COUNT query and return the integer, or 0 on any error."""
    try:
        row = await database.fetch_one(query, values or {})
        return int(row["count"]) if row and row["count"] is not None else 0
    except Exception as e:
        print(f"[ADMIN] count query failed ({query[:60]}…): {e}", flush=True)
        return 0


async def _safe_fetch(query: str, values: dict | None = None) -> list:
    """Run a SELECT query and return rows as dicts, or [] on any error."""
    try:
        rows = await database.fetch_all(query, values or {})
        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        print(f"[ADMIN] fetch query failed ({query[:60]}…): {e}", flush=True)
        return []


def _fmt(value) -> str:
    """Format a datetime/date to ISO string, or return the value as-is."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value) if value is not None else ""


# ── Main stats endpoint (keeps backward-compatible path /admin/users) ─────────

@router.get("/users")
async def get_admin_stats(_admin=Depends(get_admin_user)):
    """
    Full admin dashboard statistics.
    Path: GET /admin/users  (kept for backward compatibility with existing clients)
    """
    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()

    # ── Core counts ────────────────────────────────────────────────────────────
    total_users = await _safe_count("SELECT COUNT(*) AS count FROM users")
    new_today = await _safe_count(
        f"SELECT COUNT(*) AS count FROM users WHERE DATE(created_at) = '{today}'"
    )
    new_week = await _safe_count(
        f"SELECT COUNT(*) AS count FROM users WHERE created_at >= '{week_ago}'"
    )
    active_users = await _safe_count(
        "SELECT COUNT(*) AS count FROM users WHERE is_active = TRUE"
    )

    # ── Signals ────────────────────────────────────────────────────────────────
    active_signals = await _safe_count(
        "SELECT COUNT(*) AS count FROM signals WHERE status = 'active'"
    )
    total_signals = await _safe_count("SELECT COUNT(*) AS count FROM signals")

    # Win rate — signals marked as won vs closed
    won = await _safe_count(
        "SELECT COUNT(*) AS count FROM signals WHERE outcome = 'win'"
    )
    closed = await _safe_count(
        "SELECT COUNT(*) AS count FROM signals WHERE outcome IN ('win','loss')"
    )
    signal_win_rate = round((won / closed * 100) if closed > 0 else 0.0, 1)

    # ── Content counts ────────────────────────────────────────────────────────
    total_courses = await _safe_count("SELECT COUNT(*) AS count FROM courses")
    upcoming_webinars = await _safe_count(
        f"SELECT COUNT(*) AS count FROM webinars WHERE scheduled_at >= NOW()"
    )
    total_blog_posts = await _safe_count(
        "SELECT COUNT(*) AS count FROM blog_posts WHERE is_published = TRUE"
    )

    # ── AI usage today ────────────────────────────────────────────────────────
    # These tables may not exist yet — _safe_count returns 0 gracefully.
    ai_mentor_requests_today = await _safe_count(
        f"SELECT COUNT(*) AS count FROM ai_mentor_logs WHERE DATE(created_at) = '{today}'"
    )
    charts_analyzed_today = await _safe_count(
        f"SELECT COUNT(*) AS count FROM chart_analysis_logs WHERE DATE(created_at) = '{today}'"
    )
    journal_uploads_today = await _safe_count(
        f"SELECT COUNT(*) AS count FROM journal_uploads WHERE DATE(created_at) = '{today}'"
    )

    # ── Recent users ──────────────────────────────────────────────────────────
    recent_rows = await _safe_fetch(
        "SELECT id, email, full_name, is_active, is_admin, subscription_tier, "
        "created_at FROM users ORDER BY created_at DESC LIMIT 10"
    )
    recent_users = [
        {
            "id":                r.get("id"),
            "username":          r.get("full_name") or r.get("email", "").split("@")[0],
            "email":             r.get("email", ""),
            "is_active":         bool(r.get("is_active", True)),
            "is_admin":          bool(r.get("is_admin", False)),
            "subscription_tier": r.get("subscription_tier", "free"),
            "created_at":        _fmt(r.get("created_at")),
        }
        for r in recent_rows
    ]

    # ── User growth (last 7 days) ─────────────────────────────────────────────
    growth_rows = await _safe_fetch(
        "SELECT DATE(created_at) AS day, COUNT(*) AS count "
        "FROM users "
        f"WHERE created_at >= '{week_ago}' "
        "GROUP BY DATE(created_at) "
        "ORDER BY day"
    )
    user_growth = [
        {"date": _fmt(r.get("day")), "count": int(r.get("count", 0))}
        for r in growth_rows
    ]

    return {
        # User metrics
        "total_users":              total_users,
        "active_users":             active_users,
        "new_today":                new_today,
        "new_this_week":            new_week,
        # Signal metrics
        "active_signals":           active_signals,
        "total_signals":            total_signals,
        "signal_win_rate":          signal_win_rate,
        # Content
        "total_courses":            total_courses,
        "upcoming_webinars":        upcoming_webinars,
        "total_blog_posts":         total_blog_posts,
        # AI usage
        "ai_mentor_requests_today": ai_mentor_requests_today,
        "charts_analyzed_today":    charts_analyzed_today,
        "journal_uploads_today":    journal_uploads_today,
        # Lists
        "recent_users":             recent_users,
        "user_growth":              user_growth,
    }


# ── User management ────────────────────────────────────────────────────────────

@router.get("/users/list")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    _admin=Depends(get_admin_user),
):
    """Paginated user list with optional email/name search."""
    offset = (page - 1) * per_page

    # FIXED: use parameterized query — never interpolate user input into SQL strings
    if search:
        where = "WHERE (email ILIKE :search OR full_name ILIKE :search)"
        search_param = {"search": f"%{search}%"}
    else:
        where = ""
        search_param = {}

    total = await _safe_count(f"SELECT COUNT(*) AS count FROM users {where}", search_param)

    rows = await _safe_fetch(
        f"SELECT id, email, full_name, is_active, is_admin, subscription_tier, created_at "
        f"FROM users {where} "
        f"ORDER BY created_at DESC "
        f"LIMIT {per_page} OFFSET {offset}",
        search_param
    )

    users_out = [
        {
            "id":                r.get("id"),
            "username":          r.get("full_name") or r.get("email", "").split("@")[0],
            "email":             r.get("email", ""),
            "is_active":         bool(r.get("is_active", True)),
            "is_admin":          bool(r.get("is_admin", False)),
            "subscription_tier": r.get("subscription_tier", "free"),
            "created_at":        _fmt(r.get("created_at")),
        }
        for r in rows
    ]

    return {
        "users":    users_out,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    max(1, (total + per_page - 1) // per_page),
    }


@router.post("/users/{user_id}/toggle")
async def toggle_user_status(user_id: int, _admin=Depends(get_admin_user)):
    """Toggle a user's is_active flag (activate ↔ deactivate)."""
    try:
        row = await database.fetch_one(
            f"SELECT id, is_active FROM users WHERE id = {user_id}"
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        new_status = not bool(row["is_active"])
        await database.execute(
            f"UPDATE users SET is_active = {new_status} WHERE id = {user_id}"
        )
        return {
            "success": True,
            "user_id": user_id,
            "is_active": new_status,
            "message": "User activated" if new_status else "User deactivated",
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADMIN] toggle user {user_id} error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Trading analytics ─────────────────────────────────────────────────────────

@router.get("/trading-analytics")
async def get_trading_analytics(_admin=Depends(get_admin_user)):
    """Aggregated trading performance metrics across all signals."""
    try:
        # Top traded symbols
        symbol_rows = await _safe_fetch(
            "SELECT symbol, COUNT(*) AS count, "
            "SUM(CASE WHEN outcome='win' THEN 1 ELSE 0 END) AS wins "
            "FROM signals "
            "GROUP BY symbol "
            "ORDER BY count DESC "
            "LIMIT 8"
        )
        top_symbols = [
            {
                "symbol":   r.get("symbol", "N/A"),
                "count":    int(r.get("count", 0)),
                "wins":     int(r.get("wins", 0)),
                "win_rate": round(
                    int(r.get("wins", 0)) / int(r.get("count", 1)) * 100, 1
                ),
            }
            for r in symbol_rows
        ]

        # Signal direction split
        buy_count  = await _safe_count(
            "SELECT COUNT(*) AS count FROM signals WHERE direction='BUY'"
        )
        sell_count = await _safe_count(
            "SELECT COUNT(*) AS count FROM signals WHERE direction='SELL'"
        )

        # Signal outcomes
        wins_total   = await _safe_count(
            "SELECT COUNT(*) AS count FROM signals WHERE outcome='win'"
        )
        losses_total = await _safe_count(
            "SELECT COUNT(*) AS count FROM signals WHERE outcome='loss'"
        )
        pending      = await _safe_count(
            "SELECT COUNT(*) AS count FROM signals WHERE outcome IS NULL OR outcome='pending'"
        )

        total_closed = wins_total + losses_total
        overall_win_rate = round(
            wins_total / total_closed * 100 if total_closed > 0 else 0, 1
        )

        # Monthly signal volume (last 6 months)
        monthly_rows = await _safe_fetch(
            "SELECT TO_CHAR(created_at, 'Mon YY') AS month, COUNT(*) AS count "
            "FROM signals "
            "WHERE created_at >= NOW() - INTERVAL '6 months' "
            "GROUP BY TO_CHAR(created_at, 'Mon YY'), DATE_TRUNC('month', created_at) "
            "ORDER BY DATE_TRUNC('month', created_at)"
        )
        monthly_signals = [
            {"month": r.get("month", ""), "count": int(r.get("count", 0))}
            for r in monthly_rows
        ]

        # Average confidence
        conf_row = await _safe_fetch(
            "SELECT AVG(ai_confidence) AS avg_conf FROM signals WHERE ai_confidence IS NOT NULL"
        )
        avg_confidence = round(
            float(conf_row[0]["avg_conf"]) * 100 if conf_row and conf_row[0]["avg_conf"] else 0,
            1,
        )

        return {
            "overall_win_rate":  overall_win_rate,
            "total_signals":     wins_total + losses_total + pending,
            "wins":              wins_total,
            "losses":            losses_total,
            "pending":           pending,
            "buy_count":         buy_count,
            "sell_count":        sell_count,
            "avg_ai_confidence": avg_confidence,
            "top_symbols":       top_symbols,
            "monthly_signals":   monthly_signals,
        }

    except Exception as e:
        print(f"[ADMIN] trading analytics error: {e}", flush=True)
        # Return safe defaults so the UI never crashes
        return {
            "overall_win_rate":  0,
            "total_signals":     0,
            "wins":              0,
            "losses":            0,
            "pending":           0,
            "buy_count":         0,
            "sell_count":        0,
            "avg_ai_confidence": 0,
            "top_symbols":       [],
            "monthly_signals":   [],
        }


# ── AI system monitoring ──────────────────────────────────────────────────────

@router.get("/ai-stats")
async def get_ai_stats(_admin=Depends(get_admin_user)):
    """AI feature usage metrics across all modules."""
    today     = date.today().isoformat()
    week_ago  = (date.today() - timedelta(days=7)).isoformat()
    month_ago = (date.today() - timedelta(days=30)).isoformat()

    mentor_today    = await _safe_count(
        f"SELECT COUNT(*) AS count FROM ai_mentor_logs WHERE DATE(created_at)='{today}'"
    )
    mentor_week     = await _safe_count(
        f"SELECT COUNT(*) AS count FROM ai_mentor_logs WHERE created_at>='{week_ago}'"
    )
    charts_today    = await _safe_count(
        f"SELECT COUNT(*) AS count FROM chart_analysis_logs WHERE DATE(created_at)='{today}'"
    )
    charts_week     = await _safe_count(
        f"SELECT COUNT(*) AS count FROM chart_analysis_logs WHERE created_at>='{week_ago}'"
    )
    journals_today  = await _safe_count(
        f"SELECT COUNT(*) AS count FROM journal_uploads WHERE DATE(created_at)='{today}'"
    )
    journals_month  = await _safe_count(
        f"SELECT COUNT(*) AS count FROM journal_uploads WHERE created_at>='{month_ago}'"
    )

    # Daily AI usage trend (last 7 days)
    usage_rows = await _safe_fetch(
        "SELECT DATE(created_at) AS day, COUNT(*) AS requests "
        "FROM ai_mentor_logs "
        f"WHERE created_at >= '{week_ago}' "
        "GROUP BY DATE(created_at) "
        "ORDER BY day"
    )
    daily_usage = [
        {"date": _fmt(r.get("day")), "requests": int(r.get("requests", 0))}
        for r in usage_rows
    ]

    # Top questions/topics from mentor logs
    topic_rows = await _safe_fetch(
        "SELECT question_topic AS topic, COUNT(*) AS count "
        "FROM ai_mentor_logs "
        f"WHERE created_at >= '{month_ago}' AND question_topic IS NOT NULL "
        "GROUP BY question_topic "
        "ORDER BY count DESC "
        "LIMIT 6"
    )
    top_topics = [
        {"topic": r.get("topic", "General"), "count": int(r.get("count", 0))}
        for r in topic_rows
    ]

    return {
        "mentor_requests_today":   mentor_today,
        "mentor_requests_week":    mentor_week,
        "charts_analyzed_today":   charts_today,
        "charts_analyzed_week":    charts_week,
        "journal_uploads_today":   journals_today,
        "journal_uploads_month":   journals_month,
        "daily_ai_usage":          daily_usage,
        "top_mentor_topics":       top_topics,
    }
