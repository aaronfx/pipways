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
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from backend.database import database
from backend.auth import get_current_user

logger = logging.getLogger(__name__)

# ── Auth ──────────────────────────────────────────────────────────────────────
# #3: Shared secret between GreenXTrades bot and Pipways API.
# Set BOT_SECRET env var on Railway + PIPWAYS_BOT_SECRET on the bot VPS.
# Empty string = auth disabled (safe for dev; always set in production).
_BOT_SECRET = os.environ.get("BOT_SECRET", "")

# OAuth2 scheme for optional user authentication on signal list endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

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
    # AI-generated rationale (shown in modal Trade Idea section)
    ("rationale",       "TEXT"),
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

    # ── #16: Partial index for the primary /enhanced query ────────────────────
    # Turns the 30-second poll from a full table scan into an index seek.
    # Safe to run repeatedly — CREATE INDEX IF NOT EXISTS is idempotent.
    try:
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_enhanced
            ON signals (status, is_published, expires_at, created_at DESC)
            WHERE status = 'active' AND is_published = TRUE
        """)
        logger.info("[signals] idx_signals_enhanced verified")
    except Exception as exc:
        logger.warning(f"[signals] Index creation skipped: {exc}")

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
    pattern_lines: List[dict] = Field(default_factory=list)   # #5: explicit trendline coords
    breakout_point: Optional[BreakoutPoint] = None
    candles: List[CandleData] = Field(default_factory=list)
    is_pattern_idea: bool = False
    is_published: bool = True
    rationale: Optional[str] = None          # bot-written trade rationale for modal
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


# ── Auth helper ───────────────────────────────────────────────────────────────

def _check_bot_auth(token: Optional[str]) -> None:
    """Raise 401 if BOT_SECRET is set and the token doesn't match."""
    if _BOT_SECRET and token != _BOT_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized — invalid or missing X-Bot-Token")


# ── Columns returned by /enhanced (excludes candles — fetched on demand) ──────
# #6: candles is the heaviest column (~5 KB per signal). Grid cards don't need
# it; the modal fetches GET /api/signals/{id} which returns the full row.
_ENHANCED_COLUMNS = """
    id, symbol, direction, entry, target, stop,
    confidence, ai_confidence, asset_type, country, timeframe, status,
    pattern, pattern_name, structure, bias_d1, bias_h4, bos_m5,
    pattern_points, pattern_lines, breakout_point,
    is_pattern_idea, is_published, rationale,
    created_at, expires_at, updated_at
""".strip()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/api/signals/enhanced")
async def get_enhanced_signals(
    limit: int = 50,
    asset_type: Optional[str] = None,
    direction: Optional[str] = None,
    is_pattern_idea: Optional[bool] = None,   # #8: tab filtering server-side
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Primary endpoint for the Enhanced Signals dashboard panel.
    Returns active, published, non-expired signals newest-first.
    Candles are intentionally excluded — fetch GET /api/signals/{id} for the full row.
    Supports ?asset_type=, ?direction=, ?is_pattern_idea= query filters.

    Authentication:
      - Unauthenticated: limited to 3 most recent signals (no full data)
      - Free tier: 3 signals with full fields
      - Pro tier: all signals with full data
    """
    db = get_db()
    try:
        # Get user tier from token if available
        user_tier = "free"
        if token:
            try:
                current_user = await get_current_user(token)
                user_tier = current_user.get("subscription_tier", "free")
            except Exception:
                user_tier = "free"
        else:
            user_tier = "unauthenticated"

        # Apply tier-based limits
        tier_limit = limit
        if user_tier == "unauthenticated":
            tier_limit = min(limit, 3)
        elif user_tier == "free":
            tier_limit = min(limit, 3)
        # Pro tier: no limit imposed, use requested limit

        where_clauses = [
            "status = 'active'",
            "(expires_at IS NULL OR expires_at > NOW())",
            "is_published = TRUE",
        ]
        params: dict = {"limit": tier_limit}

        if asset_type:
            where_clauses.append("asset_type = :asset_type")
            params["asset_type"] = asset_type.lower()

        if direction and direction.upper() in ("BUY", "SELL"):
            where_clauses.append("direction = :direction")
            params["direction"] = direction.upper()

        # #8: Pattern tab sends is_pattern_idea=true to filter server-side
        if is_pattern_idea is not None:
            where_clauses.append("is_pattern_idea = :is_pattern_idea")
            params["is_pattern_idea"] = is_pattern_idea

        where_sql = " AND ".join(where_clauses)
        # #6: SELECT named columns, not SELECT * — excludes heavy candles column
        query = f"""
            SELECT {_ENHANCED_COLUMNS}
            FROM signals
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit
        """

        rows = await db.fetch_all(query, params)
        signals = [_hydrate(dict(row)) for row in rows]

        # For unauthenticated users, strip sensitive fields
        if user_tier == "unauthenticated":
            for signal in signals:
                # Remove entry/stop/target for unauthenticated users
                signal.pop("entry", None)
                signal.pop("stop", None)
                signal.pop("target", None)
                signal.pop("entry_price", None)
                signal.pop("stop_loss", None)
                signal.pop("take_profit", None)

        logger.info(f"[signals] GET /enhanced — {len(signals)} signals (tier={user_tier})")
        return signals

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] GET /enhanced error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/api/signals/winrate")
async def get_signal_winrate(
    days: int = 7,
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    #4: 7-day win rate from closed signals.
    Counts status='closed_tp' as wins, 'closed_sl' as losses.

    Authentication:
      - Unauthenticated: 404 (win rate hidden)
      - Free/Pro tier: full win rate data
    """
    # Win rate is protected — only authenticated users see it
    if not token:
        raise HTTPException(status_code=404, detail="Win rate requires authentication")

    try:
        current_user = await get_current_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    db = get_db()
    try:
        since = datetime.utcnow() - timedelta(days=days)
        row = await db.fetch_one(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'closed_tp') AS wins,
                COUNT(*) FILTER (WHERE status = 'closed_sl') AS losses
            FROM signals
            WHERE status IN ('closed_tp', 'closed_sl')
              AND updated_at >= :since
            """,
            {"since": since},
        )
        wins   = row["wins"]   if row else 0
        losses = row["losses"] if row else 0
        total  = wins + losses
        rate   = round(wins / total * 100) if total > 0 else None
        return {"wins": wins, "losses": losses, "total": total, "win_rate_pct": rate, "days": days}
    except Exception as e:
        logger.exception(f"[signals] GET /winrate error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/api/signals")
async def create_signal(
    payload: SignalIn,
    x_bot_token: Optional[str] = Header(None),   # #3: bot auth
):
    """
    Receive a signal from the GreenXTrades bot and persist it with candles.
    Requires X-Bot-Token header matching BOT_SECRET env var (if set).
    expires_in_hours is clamped to 1-168 h and computed in Python —
    fully parameterised, no string interpolation into SQL.
    """
    _check_bot_auth(x_bot_token)  # #3: raises 401 if secret mismatch
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
        # #5: Serialize pattern_lines (list of dicts, already plain JSON-safe)
        pattern_lines_json = (
            json.dumps(payload.pattern_lines)
            if payload.pattern_lines else None
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
                pattern_points, pattern_lines, breakout_point, candles,
                is_pattern_idea, is_published, rationale,
                status, created_at, expires_at
            ) VALUES (
                :symbol, :direction, :entry, :target, :stop,
                :entry_price, :take_profit, :stop_loss,
                :confidence, :ai_confidence, :asset_type, :country,
                :pattern, :pattern_name, :timeframe,
                :pattern_points, :pattern_lines, :breakout_point, :candles,
                :is_pattern_idea, :is_published, :rationale,
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
            "pattern_lines":   pattern_lines_json,
            "breakout_point":  breakout_point_json,
            "candles":         candles_json,
            "is_pattern_idea": payload.is_pattern_idea,
            "is_published":    payload.is_published,
            "rationale":       payload.rationale,
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
    token: Optional[str] = Depends(oauth2_scheme),
):
    """
    Dashboard summary panel endpoint.
    Supports ?country= and ?asset_type= query filters.

    Authentication:
      - Unauthenticated: limited to 3 most recent signals
      - Free tier: 3 signals with full fields
      - Pro tier: all signals with full data
    """
    db = get_db()
    try:
        # Get user tier from token if available
        user_tier = "free"
        if token:
            try:
                current_user = await get_current_user(token)
                user_tier = current_user.get("subscription_tier", "free")
            except Exception:
                user_tier = "free"
        else:
            user_tier = "unauthenticated"

        # Apply tier-based limits
        tier_limit = limit
        if user_tier == "unauthenticated":
            tier_limit = min(limit, 3)
        elif user_tier == "free":
            tier_limit = min(limit, 3)
        # Pro tier: no limit imposed, use requested limit

        where_clauses = [
            "status = 'active'",
            "(expires_at IS NULL OR expires_at > NOW())",
        ]
        params: dict = {"limit": tier_limit}

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

        # For unauthenticated users, strip sensitive fields
        if user_tier == "unauthenticated":
            for signal in signals:
                # Remove entry/stop/target for unauthenticated users
                signal.pop("entry", None)
                signal.pop("stop", None)
                signal.pop("target", None)
                signal.pop("entry_price", None)
                signal.pop("stop_loss", None)
                signal.pop("take_profit", None)

        logger.info(f"[signals] GET /active — {len(signals)} signals (tier={user_tier})")
        return signals

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] GET /active error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/api/signals/close-by-entry")
async def close_signal_by_entry(
    symbol: str,
    entry: float,
    outcome: str,            # "tp" | "sl" | "manual"
    close_price: float,
    x_bot_token: Optional[str] = Header(None),
):
    """
    #15: Bot calls this when MT5 closes a position.
    Looks up the signal by (symbol, entry) and marks it closed_tp / closed_sl.
    """
    _check_bot_auth(x_bot_token)
    db = get_db()
    try:
        valid_outcomes = {"tp": "closed_tp", "sl": "closed_sl", "manual": "closed_manual"}
        new_status = valid_outcomes.get(outcome.lower(), "closed_manual")
        result = await db.fetch_one(
            """
            UPDATE signals
            SET status = :status, updated_at = NOW()
            WHERE symbol = :symbol AND entry = :entry
              AND status IN ('active', 'pending')
            ORDER BY created_at DESC
            LIMIT 1
            RETURNING id, symbol, status
            """,
            {"status": new_status, "symbol": symbol.upper(), "entry": str(entry)},
        )
        if not result:
            return JSONResponse(status_code=404, content={"error": "Signal not found or already closed"})
        logger.info(f"[signals] close-by-entry {symbol} @ {entry} → {new_status}")
        return {"id": result["id"], "symbol": result["symbol"], "status": new_status, "close_price": close_price}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] close-by-entry error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# NOTE: Static-path routes (/enhanced, /active, /migrate, /expire-old, /winrate,
# /close-by-entry) are declared BEFORE /{signal_id} so FastAPI never tries to cast
# those strings as int IDs.

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


@router.post("/api/signals/{signal_id}/close")
async def close_signal_by_id(
    signal_id: int,
    outcome: str = "manual",     # "tp" | "sl" | "manual"
    close_price: Optional[float] = None,
    x_bot_token: Optional[str] = Header(None),
):
    """
    #15: Mark a specific signal as closed by its database id.
    Bot uses this when it has the signal_id cached from the POST /api/signals response.
    """
    _check_bot_auth(x_bot_token)
    db = get_db()
    try:
        valid_outcomes = {"tp": "closed_tp", "sl": "closed_sl", "manual": "closed_manual"}
        new_status = valid_outcomes.get(outcome.lower(), "closed_manual")
        result = await db.fetch_one(
            "UPDATE signals SET status = :status, updated_at = NOW() "
            "WHERE id = :id AND status IN ('active', 'pending') RETURNING id, symbol",
            {"status": new_status, "id": signal_id},
        )
        if not result:
            return JSONResponse(status_code=404, content={"error": "Signal not found or already closed"})
        logger.info(f"[signals] closed signal id={signal_id} → {new_status}")
        return {"id": signal_id, "symbol": result["symbol"], "status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[signals] close id={signal_id} error: {e}")
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
