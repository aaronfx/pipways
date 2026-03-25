"""
Trading Signals API — Complete Rebuild
Endpoints:
  GET  /signals/active        — public list (auth required)
  POST /signals/create        — admin create
  PUT  /signals/{id}          — admin update
  DELETE /signals/{id}        — admin delete
  POST /signals/{id}/close    — admin close

All status comparisons are case-insensitive.
is_published is checked as fallback publish path.
"""
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from .database import database
from .security import get_current_user, is_admin_user

try:
    from .email_service import send_signal_alert_task
    _HAS_EMAIL = True
except ImportError:
    _HAS_EMAIL = False

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────────

async def _q(sql: str, params: dict = None):
    try:
        return await database.fetch_all(sql, params or {})
    except Exception as e:
        print(f"[SIGNALS] query error: {e}", flush=True)
        return []


async def _one(sql: str, params: dict = None):
    try:
        return await database.fetch_one(sql, params or {})
    except Exception as e:
        print(f"[SIGNALS] fetch_one error: {e}", flush=True)
        return None


async def _run(sql: str, params: dict = None):
    try:
        return await database.execute(sql, params or {})
    except Exception as e:
        print(f"[SIGNALS] execute error: {e}", flush=True)
        raise HTTPException(500, f"Database error: {e}")


def _fmt_signal(row: dict) -> dict:
    return {
        "id":            row.get("id"),
        "symbol":        row.get("symbol") or "—",
        "direction":     (row.get("direction") or "—").upper(),
        "entry_price":   float(row["entry_price"]) if row.get("entry_price") is not None else 0,
        "stop_loss":     float(row["stop_loss"])   if row.get("stop_loss")   is not None else 0,
        "take_profit":   float(row["take_profit"]) if row.get("take_profit") is not None else 0,
        "timeframe":     row.get("timeframe") or "1H",
        "status":        row.get("status") or "active",
        "ai_confidence": float(row["ai_confidence"]) if row.get("ai_confidence") is not None else None,
        "analysis":      row.get("analysis") or "",
        "created_at":    row["created_at"].isoformat() if row.get("created_at") else None,
        "outcome":       row.get("outcome") or "",
    }


# ── public endpoints ──────────────────────────────────────────────────────────

@router.get("/active")
async def get_active_signals(
    limit: int = 100,
    current_user=Depends(get_current_user),
):
    """
    Return all active signals.
    Uses LOWER(status) = 'active' so 'Active', 'ACTIVE', 'active' all match.
    Falls back to simple query if is_published column doesn't exist yet.
    """
    # Try with is_published column
    rows = await _q(
        """
        SELECT id, symbol, direction, entry_price, stop_loss, take_profit,
               timeframe, status, ai_confidence, analysis, created_at, outcome
        FROM signals
        WHERE LOWER(status) = 'active'
           OR COALESCE(is_published, FALSE) = TRUE
        ORDER BY created_at DESC
        LIMIT :lim
        """,
        {"lim": limit},
    )

    # If that failed (empty because column missing), try without is_published
    if not rows:
        rows = await _q(
            """
            SELECT id, symbol, direction, entry_price, stop_loss, take_profit,
                   timeframe, status, ai_confidence, analysis, created_at, outcome
            FROM signals
            WHERE LOWER(status) = 'active'
            ORDER BY created_at DESC
            LIMIT :lim
            """,
            {"lim": limit},
        )

    result = [_fmt_signal(dict(r)) for r in rows]
    print(f"[SIGNALS] /active → {len(result)} signals", flush=True)
    return result


# ── admin endpoints ───────────────────────────────────────────────────────────

@router.post("/create")
async def create_signal(signal: dict, current_user=Depends(get_current_user)):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    # Validate required fields
    for field in ("symbol", "direction", "entry_price", "stop_loss", "take_profit"):
        if signal.get(field) is None:
            raise HTTPException(422, f"Missing required field: {field}")

    sid = await _run(
        """
        INSERT INTO signals
            (symbol, direction, entry_price, stop_loss, take_profit,
             timeframe, analysis, ai_confidence, status, created_at)
        VALUES
            (:sym, :dir, :entry, :sl, :tp,
             :tf, :anal, :conf, 'active', NOW())
        RETURNING id
        """,
        {
            "sym":   signal["symbol"].upper(),
            "dir":   signal["direction"].upper(),
            "entry": float(signal["entry_price"]),
            "sl":    float(signal["stop_loss"]),
            "tp":    float(signal["take_profit"]),
            "tf":    signal.get("timeframe") or "1H",
            "anal":  signal.get("analysis") or "",
            "conf":  signal.get("ai_confidence"),
        },
    )

    # Backfill legacy pair column if it exists
    try:
        await database.execute(
            "UPDATE signals SET pair=:p WHERE id=:id",
            {"p": signal["symbol"].upper(), "id": sid},
        )
    except Exception:
        pass

    # Queue email alerts to opted-in users (background, non-fatal)
    if _HAS_EMAIL:
        import asyncio
        asyncio.create_task(_send_signal_emails(
            signal["symbol"].upper(),
            signal["direction"].upper(),
            float(signal["entry_price"]),
            float(signal["stop_loss"]),
            float(signal["take_profit"]),
        ))

    return {"status": "created", "id": sid}


async def _send_signal_emails(symbol: str, direction: str, entry: float, sl: float, tp: float):
    """Send signal alert to all users who opted in to signal emails."""
    try:
        rows = await database.fetch_all(
            """SELECT u.id, u.email, u.full_name
               FROM users u
               LEFT JOIN user_email_preferences p ON p.user_id = u.id
               WHERE u.is_active = TRUE
               AND (p.preferences->>'signal_alerts')::boolean = true"""
        )
        for row in (rows or []):
            await send_signal_alert_task(
                row["id"], row["email"], row["full_name"] or "",
                symbol, direction, entry, sl, tp
            )
    except Exception as e:
        print(f"[SIGNAL EMAIL] Error: {e}", flush=True)


@router.put("/{signal_id}")
async def update_signal(signal_id: int, signal: dict, current_user=Depends(get_current_user)):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    if not await _one("SELECT id FROM signals WHERE id=:id", {"id": signal_id}):
        raise HTTPException(404, "Signal not found")

    await _run(
        """
        UPDATE signals
        SET symbol=:sym, direction=:dir, entry_price=:entry,
            stop_loss=:sl, take_profit=:tp, timeframe=:tf,
            analysis=:anal, ai_confidence=:conf, status=:status
        WHERE id=:id
        """,
        {
            "sym":    signal.get("symbol", "").upper(),
            "dir":    signal.get("direction", "BUY").upper(),
            "entry":  float(signal.get("entry_price", 0)),
            "sl":     float(signal.get("stop_loss", 0)),
            "tp":     float(signal.get("take_profit", 0)),
            "tf":     signal.get("timeframe") or "1H",
            "anal":   signal.get("analysis") or "",
            "conf":   signal.get("ai_confidence"),
            "status": signal.get("status") or "active",
            "id":     signal_id,
        },
    )
    return {"message": "Signal updated"}


@router.delete("/{signal_id}")
async def delete_signal(signal_id: int, current_user=Depends(get_current_user)):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")
    await _run("DELETE FROM signals WHERE id=:id", {"id": signal_id})
    return {"message": "Signal deleted"}


@router.post("/{signal_id}/close")
async def close_signal(
    signal_id: int,
    outcome: Optional[str] = "closed",
    current_user=Depends(get_current_user),
):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")
    await _run(
        "UPDATE signals SET status='closed', outcome=:outcome WHERE id=:id",
        {"outcome": outcome, "id": signal_id},
    )
    return {"message": f"Signal closed ({outcome})"}
