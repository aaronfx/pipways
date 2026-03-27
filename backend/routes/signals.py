# signals.py  —  Pipways backend route for GreenXTrades signal ingestion
# Deploy to: routes/signals.py
#
# Mount in main.py:
#
#   from routes import signals
#   app.include_router(signals.router)   # no prefix — route is /signals
#
# ⚠️  Do NOT add prefix="/signals" — that would make the route /signals/signals.

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging
import json

logger = logging.getLogger(__name__)

# redirect_slashes=False prevents FastAPI from creating the /signals/ redirect
# that can silently convert POST → GET through a proxy.
router = APIRouter(redirect_slashes=False)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_database():
    """Get database connection from main app"""
    from backend.database import database
    return database


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class PatternPoint(BaseModel):
    time: int
    price: float

class BreakoutPoint(BaseModel):
    time: int
    price: float

class SignalIn(BaseModel):
    # Core
    symbol: str
    direction: str                          # "BUY" | "SELL"
    entry: str                              # sent as string from bot
    target: str                             # TP
    stop: str                               # SL

    # Metadata
    confidence: int = 50
    asset_type: str = "forex"
    country: str = "all"
    expires_in_hours: int = 24

    # Pattern / structure
    pattern: str = "BREAKOUT"
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
    bos_m5: Optional[str] = None

    # Test signal marker
    test_signal: Optional[bool] = False

    class Config:
        extra = "allow"     # ignore any extra fields the bot adds in future


# ═══════════════════════════════════════════════════════════════════════════════
# POST /signals — Create signal from bot
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/signals")
async def create_signal(payload: SignalIn):
    """
    Receive a structured SMC signal from GreenXTrades bot and save to DB.
    Returns 201 on success so the bot logs ✅.
    """
    db = get_database()
    
    try:
        logger.info(
            f"[signals] ▶ Received {payload.symbol} {payload.direction} "
            f"@ {payload.entry} | confidence={payload.confidence} "
            f"test={payload.test_signal}"
        )

        # Convert pattern_points to JSON string
        pattern_points_json = None
        if payload.pattern_points:
            pattern_points_json = json.dumps([p.dict() for p in payload.pattern_points])

        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)

        # Insert into database
        query = """
            INSERT INTO signals (
                symbol, direction, entry, target, stop,
                confidence, ai_confidence, asset_type, country,
                pattern, timeframe, is_pattern_idea,
                pattern_points, status, is_published,
                created_at, expires_at
            ) VALUES (
                :symbol, :direction, :entry, :target, :stop,
                :confidence, :confidence, :asset_type, :country,
                :pattern, :timeframe, :is_pattern_idea,
                :pattern_points, 'active', TRUE,
                :created_at, :expires_at
            )
            RETURNING id
        """

        params = {
            "symbol": payload.symbol,
            "direction": payload.direction.upper(),
            "entry": payload.entry,
            "target": payload.target,
            "stop": payload.stop,
            "confidence": payload.confidence,
            "asset_type": payload.asset_type,
            "country": payload.country,
            "pattern": payload.pattern,
            "timeframe": payload.timeframe,
            "is_pattern_idea": payload.is_pattern_idea,
            "pattern_points": pattern_points_json,
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
        }

        result = await db.fetch_one(query, params)
        signal_id = result["id"] if result else None

        logger.info(
            f"[signals] ✅ {payload.symbol} {payload.direction} saved | id={signal_id}"
        )

        return JSONResponse(
            status_code=201,
            content={
                "ok": True,
                "signal_id": signal_id,
                "symbol": payload.symbol,
                "direction": payload.direction,
                "message": "Signal received and saved.",
            },
        )

    except Exception as e:
        logger.exception(f"[signals] ❌ Failed to save signal: {e}")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# GET /signals/enhanced — Read signals for frontend dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/signals/enhanced")
async def get_enhanced_signals(limit: int = 50):
    """
    Return active, non-expired signals.
    Called by dashboard to populate the Enhanced Signals panel.
    """
    db = get_database()
    
    try:
        query = """
            SELECT * FROM signals 
            WHERE status = 'active'
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            LIMIT :limit
        """
        
        rows = await db.fetch_all(query, {"limit": limit})
        
        if not rows:
            logger.info("[signals] GET /signals/enhanced — no active signals")
            return []
        
        # Convert rows to dicts and parse JSON fields
        signals = []
        for row in rows:
            signal = dict(row)
            
            # Parse JSON fields if present
            if signal.get('pattern_points'):
                try:
                    signal['pattern_points'] = json.loads(signal['pattern_points'])
                except:
                    signal['pattern_points'] = None
                    
            if signal.get('pattern_lines'):
                try:
                    signal['pattern_lines'] = json.loads(signal['pattern_lines'])
                except:
                    signal['pattern_lines'] = None
            
            # Convert datetime to ISO string for JSON
            for key in ['created_at', 'expires_at', 'updated_at']:
                if signal.get(key) and hasattr(signal[key], 'isoformat'):
                    signal[key] = signal[key].isoformat()
            
            signals.append(signal)
        
        logger.info(f"[signals] GET /signals/enhanced — returning {len(signals)} signals")
        return signals

    except Exception as e:
        logger.exception(f"[signals] GET /signals/enhanced error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# GET /signals/active — Filtered signals (legacy compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/signals/active")
async def get_active_signals(
    country: str = "all",
    asset_type: str = "forex",
    limit: int = 50
):
    """
    Return filtered active signals. Has default params to avoid 422 errors.
    """
    db = get_database()
    
    try:
        query = """
            SELECT * FROM signals 
            WHERE status = 'active'
            AND (expires_at IS NULL OR expires_at > NOW())
        """
        params = {"limit": limit}
        
        if country and country != "all":
            query += " AND country = :country"
            params["country"] = country
            
        if asset_type and asset_type != "all":
            query += " AND asset_type = :asset_type"
            params["asset_type"] = asset_type
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        
        rows = await db.fetch_all(query, params)
        signals = [dict(row) for row in rows] if rows else []
        
        # Convert datetime fields
        for signal in signals:
            for key in ['created_at', 'expires_at', 'updated_at']:
                if signal.get(key) and hasattr(signal[key], 'isoformat'):
                    signal[key] = signal[key].isoformat()
        
        logger.info(f"[signals] GET /signals/active — returning {len(signals)} signals")
        return signals

    except Exception as e:
        logger.exception(f"[signals] GET /signals/active error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# GET /signals/{id} — Single signal
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/signals/{signal_id}")
async def get_signal(signal_id: int):
    """Return a single signal by ID."""
    db = get_database()
    
    try:
        query = "SELECT * FROM signals WHERE id = :signal_id"
        row = await db.fetch_one(query, {"signal_id": signal_id})
        
        if not row:
            return JSONResponse(status_code=404, content={"error": "Signal not found"})
        
        signal = dict(row)
        
        # Parse JSON fields
        if signal.get('pattern_points'):
            try:
                signal['pattern_points'] = json.loads(signal['pattern_points'])
            except:
                pass
                
        if signal.get('pattern_lines'):
            try:
                signal['pattern_lines'] = json.loads(signal['pattern_lines'])
            except:
                pass
        
        # Convert datetime fields
        for key in ['created_at', 'expires_at', 'updated_at']:
            if signal.get(key) and hasattr(signal[key], 'isoformat'):
                signal[key] = signal[key].isoformat()
        
        return signal

    except Exception as e:
        logger.exception(f"[signals] GET /signals/{signal_id} error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /signals/{id} — Soft delete (mark inactive)
# ═══════════════════════════════════════════════════════════════════════════════

@router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: int):
    """Soft delete a signal (mark as inactive)."""
    db = get_database()
    
    try:
        query = "UPDATE signals SET status = 'inactive' WHERE id = :signal_id RETURNING id"
        result = await db.fetch_one(query, {"signal_id": signal_id})
        
        if not result:
            return JSONResponse(status_code=404, content={"error": "Signal not found"})
        
        logger.info(f"[signals] ✅ Deleted signal #{signal_id}")
        return {"id": signal_id, "status": "deleted"}

    except Exception as e:
        logger.exception(f"[signals] DELETE /signals/{signal_id} error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# POST /signals/expire-old — Cleanup expired signals
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/signals/expire-old")
async def expire_old_signals():
    """Mark expired signals as inactive. Can be called by cron job."""
    db = get_database()
    
    try:
        query = """
            UPDATE signals 
            SET status = 'expired' 
            WHERE status = 'active' 
            AND expires_at < NOW()
            RETURNING id
        """
        rows = await db.fetch_all(query)
        count = len(rows) if rows else 0
        
        logger.info(f"[signals] ✅ Expired {count} old signals")
        return {"expired_count": count}

    except Exception as e:
        logger.exception(f"[signals] expire-old error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
