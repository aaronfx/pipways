# signals.py  —  Pipways backend route for GreenXTrades signal ingestion
#
# Mount in main.py:
#
#   from routes import signals
#   app.include_router(signals.router)   # no prefix — route is /signals
#
# Or if you use a prefix:
#
#   app.include_router(signals.router, prefix="")   # still /signals
#
# ⚠️  Do NOT add prefix="/signals" — that would make the route /signals/signals.
#
# FastAPI's redirect behaviour:
#   By default FastAPI redirects /signals/ → /signals with HTTP 307.
#   The requests library follows 307 redirects but KEEPS the original method (POST).
#   However some proxies (nginx, Render's edge) convert 307 → 302 which drops to GET.
#   Fix: always POST to /signals (no trailing slash) and set redirect_slashes=False below.

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# redirect_slashes=False prevents FastAPI from creating the /signals/ redirect
# that can silently convert POST → GET through a proxy.
router = APIRouter(redirect_slashes=False)


# ── Request schema ─────────────────────────────────────────────────────────────
# All fields match exactly what GreenXTrades sends in build_pipways_payload().
# `Any` fields are optional extras that may be absent — they won't cause a 422.

class PatternPoint(BaseModel):
    time:  int
    price: float

class BreakoutPoint(BaseModel):
    time:  int
    price: float

class SignalIn(BaseModel):
    # Core
    symbol:    str
    direction: str                          # "BUY" | "SELL"
    entry:     str                          # sent as string from bot
    target:    str                          # TP
    stop:      str                          # SL

    # Metadata
    confidence:       int   = 50
    asset_type:       str   = "forex"
    country:          str   = "all"
    expires_in_hours: int   = 24

    # Pattern / structure
    pattern:   str = "BREAKOUT"
    structure: str = "BOS"
    timeframe: str = "M5"

    # Chart overlay
    pattern_points: List[PatternPoint] = Field(default_factory=list)
    breakout_point: Optional[BreakoutPoint] = None

    # Enhanced Signals routing — MUST be True for dashboard to show the signal
    is_pattern_idea: bool = False

    # SMC context (informational)
    bias_d1: Optional[str] = None
    bias_h4: Optional[str] = None
    bos_m5:  Optional[str] = None

    # Test signal marker
    test_signal: Optional[bool] = False

    class Config:
        extra = "allow"     # ignore any extra fields the bot adds in future


# ── POST /signals ──────────────────────────────────────────────────────────────
@router.post("/signals")                   # ← must be exactly this, no trailing slash
async def create_signal(payload: SignalIn):
    """
    Receive a structured SMC signal from GreenXTrades bot and save to DB.
    Returns 201 on success so the bot logs ✅.
    """
    try:
        logger.info(
            f"[signals] ▶ Received {payload.symbol} {payload.direction} "
            f"@ {payload.entry} | confidence={payload.confidence} "
            f"test={payload.test_signal}"
        )

        # ── TODO: replace with your actual DB insert ───────────────────────────
        # Example with SQLAlchemy async session:
        #
        #   signal = Signal(
        #       symbol          = payload.symbol,
        #       direction       = payload.direction,
        #       entry           = float(payload.entry),
        #       target          = float(payload.target),
        #       stop            = float(payload.stop),
        #       confidence      = payload.confidence,
        #       asset_type      = payload.asset_type,
        #       pattern         = payload.pattern,
        #       structure       = payload.structure,
        #       timeframe       = payload.timeframe,
        #       is_pattern_idea = payload.is_pattern_idea,
        #       test_signal     = payload.test_signal or False,
        #       expires_at      = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours),
        #       created_at      = datetime.now(timezone.utc),
        #   )
        #   db.add(signal)
        #   await db.commit()
        #   await db.refresh(signal)
        #   signal_id = signal.id
        #
        # ──────────────────────────────────────────────────────────────────────

        signal_id = None   # replace with real DB id after insert

        logger.info(
            f"[signals] ✅ {payload.symbol} {payload.direction} saved | id={signal_id}"
        )

        return JSONResponse(
            status_code=201,
            content={
                "ok":        True,
                "signal_id": signal_id,
                "symbol":    payload.symbol,
                "direction": payload.direction,
                "message":   "Signal received and saved.",
            },
        )

    except Exception as e:
        logger.exception(f"[signals] ❌ Failed to save signal: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)},
        )


# ── GET /signals/enhanced  (read-only — for frontend dashboard) ────────────────
@router.get("/signals/enhanced")
async def get_enhanced_signals(limit: int = 50):
    """
    Return active, non-expired signals with is_pattern_idea=True.
    Called by dashboard.html to populate the Enhanced Signals panel.
    """
    try:
        # TODO: replace with real DB query, e.g.:
        #   signals = await db.execute(
        #       select(Signal)
        #       .where(Signal.is_pattern_idea == True)
        #       .where(Signal.expires_at > datetime.now(timezone.utc))
        #       .order_by(Signal.created_at.desc())
        #       .limit(limit)
        #   )
        #   rows = signals.scalars().all()
        #   return [row.to_dict() for row in rows]

        return JSONResponse(status_code=200, content={"signals": [], "count": 0})

    except Exception as e:
        logger.exception(f"[signals] GET /signals/enhanced error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
