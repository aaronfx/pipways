"""
Signals router — Pipways
All routes served under /api/signals/* (explicit paths, no router prefix).
Import source: backend.database (single, clean, no fallback).
Signal source: GreenXTrades bot only. No seed data here.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import database

logger = logging.getLogger(__name__)

# ── Router ────────────────────────────────────────────────────────────────────
# No prefix — full paths are declared on each route decorator.
# This prevents the double-prefix bug (/api/api/signals/...) and
# avoids the 302-redirect trap caused by the SPA catch-all 404 handler.
router = APIRouter(tags=["signals"])


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_db():
    if not database:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return database


def _parse_json_field(value):
    """Safely parse a JSON string field; return None on failure."""
    if value is None:
        return None
    if not isinstance(value, str):
        return value          # already parsed (e.g. asyncpg returned a list)
    try:
        return json.loads(value)
    except Exception:
        return None


def _hydrate(row: dict) -> dict:
    """Parse JSON text columns so the frontend receives real arrays/objects."""
    for field in ("pattern_points", "candles", "breakout_point", "pattern_lines"):
        if field in row:
            row[field] = _parse_json_field(row[field])
    return row


# ── Pydantic models ───────────────────────────────────────────────────────────
class SignalCreate(BaseModel):
    symbol: str
    direction: str
    entry: str
    target: str
    stop: str
    entry_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence: Optional[int] = 70
    ai_confidence: Optional[int] = 70
    asset_type: Optional[str] = "forex"
    country: Optional[str] = "all"
    pattern: Optional[str] = "BREAKOUT"
    pattern_name: Optional[str] = "Breakout"
    timeframe: Optional[str] = "M5"
    pattern_points: Optional[str] = None   # JSON string
    pattern_lines: Optional[str] = None    # JSON string
    candles: Optional[str] = None          # JSON string
    breakout_point: Optional[str] = None   # JSON string
    is_pattern_idea: Optional[bool] = True
    is_published: Optional[bool] = True
    expires_at: Optional[datetime] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/api/signals/enhanced")
async def get_enhanced_signals(
    limit: int = 50,
    asset_type: Optional[str] = None,
    direction: Optional[str] = None,
):
    """
    Primary endpoint consumed by the Enhanced Signals dashboard panel.
    Returns active, published, non-expired signals in descending creation order.
    """
    try:
        db = get_db()

        # Build query — use raw SELECT * for schema-lag resilience
        # (avoids missing-column errors when a new migration hasn't landed yet)
        where_clauses = [
            "status = 'active'",
            "is_published = TRUE",
            "(expires_at IS NULL OR expires_at > NOW())",
        ]

        if asset_type:
            # Simple equality; asset_type comes from our own query param, not user input
            where_clauses.append(f"asset_type = '{asset_type.lower()}'")

        if direction and direction.upper() in ("BUY", "SELL"):
            where_clauses.append(f"direction = '{direction.upper()}'")

        where_sql = " AND ".join(where_clauses)

        # Use :limit so database.py's param replacement maps it to $1
        query = f"""
            SELECT * FROM signals
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit
        """

        rows = await db.fetch_all(query, {"limit": limit})
        return [_hydrate(dict(row)) for row in rows]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[signals] Error in /api/signals/enhanced: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch enhanced signals")


@router.post("/api/signals")
async def create_signal(payload: SignalCreate):
    """
    Called by the GreenXTrades bot via the signal bridge.
    Accepts a fully-formed signal and inserts it into the database.
    """
    try:
        db = get_db()

        data = payload.dict()

        # Default expiry: 4 hours from now
        if data.get("expires_at") is None:
            data["expires_at"] = datetime.utcnow() + timedelta(hours=4)

        # Ensure JSON fields are stored as strings
        for field in ("pattern_points", "pattern_lines", "candles", "breakout_point"):
            val = data.get(field)
            if val is not None and not isinstance(val, str):
                data[field] = json.dumps(val)

        created = await db.create_signal(data)
        return {"success": True, "signal": dict(created)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[signals] Error in POST /api/signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create signal")


@router.get("/api/signals/active")
async def get_active_signals(limit: int = 50):
    """Alias for active signals — identical result to /api/signals/enhanced."""
    try:
        db = get_db()
        rows = await db.get_active_signals(limit=limit)
        return [_hydrate(row) for row in rows]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[signals] Error in /api/signals/active: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch active signals")


# NOTE: This route MUST be declared before /{signal_id} to avoid FastAPI
# matching "active" or "enhanced" as an integer ID.
@router.get("/api/signals/{signal_id}")
async def get_signal(signal_id: int):
    """Return a single signal by primary key."""
    try:
        db = get_db()
        signal = await db.get_signal_by_id(signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
        return _hydrate(signal)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[signals] Error fetching signal {signal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch signal")


@router.delete("/api/signals/{signal_id}")
async def expire_signal(signal_id: int):
    """Soft-delete a signal by setting its status to 'expired'."""
    try:
        db = get_db()
        # Use :id so database.py maps it to $1
        await db.execute(
            "UPDATE signals SET status = 'expired', updated_at = NOW() WHERE id = :id",
            {"id": signal_id},
        )
        return {"success": True, "message": f"Signal {signal_id} expired"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[signals] Error expiring signal {signal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to expire signal")
