"""
Signals router — Pipways
Deploy to: backend/routes/signals.py

All routes at /api/signals/* (explicit full paths, no router prefix).
Single clean import from backend.database — no fallbacks.
Signal source: GreenXTrades bot only. No seed data.

Migration:
  Call `await run_signals_migration()` from main.py lifespan startup.
  It is fully idempotent — ADD COLUMN IF NOT EXISTS per column, one at a time.
  Also exposed as POST /api/signals/migrate for one-shot manual recovery.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.database import database

logger = logging.getLogger(__name__)

# ── Router ────────────────────────────────────────────────────────────────────
# No prefix on the router — every path is declared in full on the decorator.
# Prevents the double-prefix bug (/api/api/signals/...) and the 302-redirect
# trap caused by the SPA catch-all 404 handler in main.py.
router = APIRouter(redirect_slashes=False, tags=["signals"])


# ── DB helper ─────────────────────────────────────────────────────────────────
def get_db():
    if not database:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return database


# ── Schema migration ──────────────────────────────────────────────────────────

# Every column the signals table must have.
# Declared as (name, postgres_type_and_default) pairs.
# ADD COLUMN IF NOT EXISTS is run individually so a pre-existing column never
# causes the rest to be skipped — the bug that caused the HTTP 500 on pattern_name.
_SIGNALS_COLUMNS: list = [
    # Core price fields
    ("entry_price",     "NUMERIC(20, 8)"),
    ("take_profit",     "NUMERIC(20, 8)"),
    ("stop_loss",       "NUMERIC(20, 8)"),
    ("ai_confidence",   "INTEGER DEFAULT 50"),
    # Classification
    ("asset_type",      "TEXT DEFAULT 'forex'"),
    ("country",         "TEXT DEFAULT 'all'"),
    ("timeframe",       "TEXT DEFAULT 'M5'"),
    ("status",          "TEXT DEFAULT 'active'"),
    # SMC / pattern metadata
    ("pattern",         "TEXT"),
    ("pattern_name",    "TEXT"),          # v9.24 — was missing, caused HTTP 500
    ("structure",       "TEXT"),
    ("bias_d1",         "TEXT"),
    ("bias_h4",         "TEXT"),
    ("bos_m5",          "TEXT"),
    # JSON columns
    ("pattern_points",  "JSONB DEFAULT '[]'"),
    ("pattern_lines",   "JSONB DEFAULT '[]'"),  # v9.24
    ("breakout_point",  "JSONB"),
    ("candles",         "JSONB DEFAULT '[]'"),
    # Flags
    ("is_pattern_idea", "BOOLEAN DEFAULT FALSE"),
    ("is_published",    "BOOLEAN DEFAULT TRUE"),
    # Timestamps
    ("expires_at",      "TIMESTAMPTZ"),
    ("updated_at",      "TIMESTAMPTZ"),
]


async def run_signals_migration() -> dict:
    """
    Idempotent schema migration for the signals table.

    Runs one ALTER TABLE … ADD COLUMN IF NOT EXISTS per column so that:
      - Adding a brand-new column never silently skips sibling columns.
      - Safe to call on every Railway deploy / app startup.
      - Returns a summary dict for logging / the /migrate endpoint.

    Call from main.py lifespan:
        from backend.routes.signals import run_signals_migration
        async with lifespan(app):
            await run_signals_migration()
    """
    db = database
    if not db:
        raise RuntimeError("Database not initialised — cannot run signals migration")

    applied: list[str] = []
    skipped: list[str] = []

    for col_name, col_def in _SIGNALS_COLUMNS:
        try:
            await db.execute(
                f"ALTER TABLE signals ADD COLUMN IF NOT EXISTS {col_name} {col_def};"
            )
            applied.append(col_name)
        except Exception as exc:
            # Log but continue — one bad column must not abort the rest
            logger.error(f"[signals] migration failed for column '{col_name}': {exc}")
            skipped.append(col_name)

    summary = {
        "total":   len(_SIGNALS_COLUMNS),
        "applied": len(applied),
        "skipped": len(skipped),
        "columns": applied,
        "errors":  skipped,
    }
    if skipped:
        logger.warning(f"[signals] Migration completed with errors: {summary}")
    else:
        logger.info(f"[signals] Migration OK — {len(applied)} columns verified")

    return summary


# ── Pydantic models ───────────────────────────────────────────────────────────

class PatternPoint(BaseModel):
    time: int
    price: float


class BreakoutPoint(BaseModel):
    time: int
    price: float


class CandleData(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float


class SignalIn(BaseModel):
    """Payload sent by the GreenXTrades bot signal bridge."""
    symbol: str
    direction: str
    entry: str
    target: str
    stop: str
    confidence: int = 50
    asset_type: str = "forex"
    country: str = "all"
    expires_in_hours: int = 24
    pattern: str = "BREAKOUT"
    pattern_name: Optional[str] = "Breakout"
    structure: str = "BOS"
    timeframe: str = "M5"
    pattern_points: List[PatternPoint] = Field(default_factory=list)
    breakout_point: Optional[BreakoutPoint] = None
    candles: List[CandleData] = Field(default_factory=list)
    is_pattern_idea: bool = False
    is_published: bool = True
    bias_d1: Optional[str] = None
    bias_h4: Optional[str] = None
    bos_m5: Optional[str] = None
    test_signal: Optional[bool] = False

    class Config:
        extra = "allow"   # forward-compatible: bot can send new fields freely


# ── Serialisation helpers ─────────────────────────────────────────────────────

def _parse_json_field(value):
    """Safely parse a JSON string field; pass through if already decoded."""
    if value is None:
        return None
    if not isinstance(value, str):
        return value          # asyncpg may have already decoded it
    try:
        return json.loads(value)
    except Exception:
        return None


def _parse_candles(value, symbol: str = ""):
    """
    Parse candles JSON with validation — must be a non-empty list.
    Logs candle count for observability.
    """
    if not value:
        return None
    parsed = _parse_json_field(value)
    if isinstance(parsed, list) and len(parsed) > 0:
        logger.debug(f"[signals] 📊 {len(parsed)} candles for {symbol}")
        return parsed
    return None


def _serialize_datetimes(signal: dict) -> dict:
    """Convert datetime columns to ISO-8601 strings for JSON serialisation."""
    for key in ("created_at", "expires_at", "updated_at"):
        val = signal.get(key)
        if val and hasattr(val, "isoformat"):
            signal[key] = val.isoformat()
    return signal


def _hydrate(row: dict) -> dict:
    """
    Full signal hydration:
      - parse pattern_points / breakout_point / pattern_lines JSON
      - parse & validate candles JSON (must be non-empty list)
      - convert datetime fields to ISO strings
    """
    symbol = row.get("symbol", "")

    for field in ("pattern_points", "breakout_point", "pattern_lines"):
        if field in row:
            row[field] = _parse_json_field(row[field])

    row["candles"] = _parse_candles(row.get("candles"), symbol)
    _serialize_datetimes(row)
    return row


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/api/signals/enhanced")
async def get_enhanced_signals(
    limit: int = 50,
    asset_type: Optional[str] = None,
    direction: Optional[str] = None,
):
    """
    Primary endpoint for the Enhanced Signals dashboard panel.
    Returns active, published, non-expired signals newest-first.
    Supports optional ?asset_type= and ?direction= query filters.
    """
    db = get_db()
    try:
        where_clauses = [
            "status = 'active'",
            "(expires_at IS NULL OR expires_at > NOW())",
        ]
        params: dict = {"limit": limit}

        if asset_type:
            where_clauses.append("asset_type = :asset_type")
            params["asset_type"] = asset_type.lower()

        if direction and direction.upper() in ("BUY", "SELL"):
            where_clauses.append("direction = :direction")
            params["direction"] = direction.upper()

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT * FROM signals
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit
        """

        rows = await db.fetch_all(query, params)
        signals = [_hydrate(dict(row)) for row in rows]

        total_candles = sum(len(s.get("candles") or []) for s in signals)
        logger.info(
            f"[signals] GET /enhanced — {len(signals)} signals, {total_candles} candles total"
        )
        return signals

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] GET /enhanced error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/api/signals")
async def create_signal(payload: SignalIn):
    """
    Receive a signal from the GreenXTrades bot and persist it with candles.
    expires_in_hours is clamped to 1-168 h and computed in Python —
    fully parameterised, no string interpolation into SQL.
    """
    db = get_db()
    try:
        logger.info(
            f"[signals] > {payload.symbol} {payload.direction} @ {payload.entry} "
            f"| candles={len(payload.candles)} test={payload.test_signal}"
        )

        # Serialise typed sub-models to JSON strings
        pattern_points_json = (
            json.dumps([p.dict() for p in payload.pattern_points])
            if payload.pattern_points else None
        )
        breakout_point_json = (
            json.dumps(payload.breakout_point.dict())
            if payload.breakout_point else None
        )
        candles_json = (
            json.dumps([c.dict() for c in payload.candles])
            if payload.candles else None
        )

        if candles_json:
            logger.info(f"[signals] Storing {len(payload.candles)} candles for {payload.symbol}")

        # Clamp expires_in_hours — min 1 h, max 7 days
        expires_hours = max(1, min(int(payload.expires_in_hours), 168))
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        entry_price = float(payload.entry)  if payload.entry  else 0.0
        take_profit = float(payload.target) if payload.target else 0.0
        stop_loss   = float(payload.stop)   if payload.stop   else 0.0
        conf_int    = int(payload.confidence)

        query = """
            INSERT INTO signals (
                symbol, direction, entry, target, stop,
                entry_price, take_profit, stop_loss,
                confidence, ai_confidence, asset_type, country,
                pattern, pattern_name, timeframe,
                pattern_points, breakout_point, candles,
                is_pattern_idea, is_published,
                status, created_at, expires_at
            ) VALUES (
                :symbol, :direction, :entry, :target, :stop,
                :entry_price, :take_profit, :stop_loss,
                :confidence, :ai_confidence, :asset_type, :country,
                :pattern, :pattern_name, :timeframe,
                :pattern_points, :breakout_point, :candles,
                :is_pattern_idea, :is_published,
                'active', NOW(), :expires_at
            )
            RETURNING id
        """

        params = {
            "symbol":          payload.symbol,
            "direction":       payload.direction.upper(),
            "entry":           payload.entry,
            "target":          payload.target,
            "stop":            payload.stop,
            "entry_price":     entry_price,
            "take_profit":     take_profit,
            "stop_loss":       stop_loss,
            "confidence":      conf_int,
            "ai_confidence":   conf_int,
            "asset_type":      payload.asset_type,
            "country":         payload.country,
            "pattern":         payload.pattern,
            "pattern_name":    payload.pattern_name or "Breakout",
            "timeframe":       payload.timeframe,
            "pattern_points":  pattern_points_json,
            "breakout_point":  breakout_point_json,
            "candles":         candles_json,
            "is_pattern_idea": payload.is_pattern_idea,
            "is_published":    payload.is_published,
            "expires_at":      expires_at,
        }

        result = await db.fetch_one(query, params)
        signal_id = result["id"] if result else None
        logger.info(f"[signals] OK {payload.symbol} saved | id={signal_id}")

        return JSONResponse(
            status_code=201,
            content={
                "ok":             True,
                "signal_id":      signal_id,
                "symbol":         payload.symbol,
                "candles_stored": len(payload.candles),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] FAIL to save {payload.symbol}: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@router.get("/api/signals/active")
async def get_active_signals(
    country: str = "all",
    asset_type: str = "all",
    limit: int = 50,
):
    """
    Dashboard summary panel endpoint.
    Supports ?country= and ?asset_type= query filters.
    """
    db = get_db()
    try:
        where_clauses = [
            "status = 'active'",
            "(expires_at IS NULL OR expires_at > NOW())",
        ]
        params: dict = {"limit": limit}

        if country and country != "all":
            where_clauses.append("country = :country")
            params["country"] = country

        if asset_type and asset_type != "all":
            where_clauses.append("asset_type = :asset_type")
            params["asset_type"] = asset_type

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT * FROM signals
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit
        """

        rows = await db.fetch_all(query, params)
        signals = [_hydrate(dict(row)) for row in rows]
        logger.info(f"[signals] GET /active — {len(signals)} signals")
        return signals

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] GET /active error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# NOTE: Static-path routes (/enhanced, /active, /migrate, /expire-old) are
# declared BEFORE /{signal_id} so FastAPI never tries to cast those strings as int IDs.

@router.post("/api/signals/migrate")
async def migrate_signals_table():
    """
    One-shot admin endpoint — runs run_signals_migration() on demand.

    Use this immediately after a deploy that adds new DB columns, or any time
    a POST /api/signals returns HTTP 500 with "column X does not exist".

    Not authenticated (internal Railway network only in production).
    Safe to call repeatedly — fully idempotent.
    """
    try:
        summary = await run_signals_migration()
        status_code = 200 if not summary["errors"] else 207  # 207 = partial success
        return JSONResponse(status_code=status_code, content={"ok": True, **summary})
    except Exception as e:
        logger.exception(f"[signals] /migrate endpoint error: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})




@router.get("/api/signals/{signal_id}")
async def get_signal(signal_id: int):
    """Return a single signal by primary key, fully hydrated."""
    db = get_db()
    try:
        row = await db.fetch_one(
            "SELECT * FROM signals WHERE id = :id", {"id": signal_id}
        )
        if not row:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        return _hydrate(dict(row))

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] GET /{signal_id} error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.delete("/api/signals/{signal_id}")
async def delete_signal(signal_id: int):
    """Soft-delete: sets status to 'inactive'."""
    db = get_db()
    try:
        result = await db.fetch_one(
            "UPDATE signals SET status = 'inactive', updated_at = NOW() "
            "WHERE id = :id RETURNING id",
            {"id": signal_id},
        )
        if not result:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        return {"id": signal_id, "status": "deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] DELETE /{signal_id} error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/api/signals/expire-old")
async def expire_old_signals():
    """
    Bulk-expires signals whose expires_at has passed.
    Call from a Railway cron job or scheduler.
    """
    db = get_db()
    try:
        rows = await db.fetch_all(
            "UPDATE signals SET status = 'expired', updated_at = NOW() "
            "WHERE status = 'active' AND expires_at < NOW() "
            "RETURNING id"
        )
        count = len(rows) if rows else 0
        logger.info(f"[signals] Expired {count} old signals")
        return {"expired_count": count}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] expire-old error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
