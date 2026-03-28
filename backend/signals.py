"""
Signals API routes for Pipways
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["signals"])

# Import database - multiple fallback patterns
try:
    from backend.database import get_database, database
except ImportError:
    try:
        from database import get_database, database
    except ImportError as e:
        logger.error(f"[signals] Cannot import database: {e}")
        get_database = None
        database = None

# Pydantic models
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
    structure: str = "BOS"
    timeframe: str = "M5"
    pattern_points: List[PatternPoint] = Field(default_factory=list)
    breakout_point: Optional[BreakoutPoint] = None
    candles: List[CandleData] = Field(default_factory=list)
    is_pattern_idea: bool = True
    pattern_name: Optional[str] = "Breakout"
    bias_d1: Optional[str] = None
    bias_h4: Optional[str] = None
    bos_m5: Optional[str] = None
    test_signal: Optional[bool] = False

    class Config:
        extra = "allow"

def get_db():
    """Get database instance"""
    if database:
        return database
    if get_database:
        return get_database()
    raise HTTPException(status_code=500, detail="Database not initialized")

@router.post("/signals")
async def create_signal(payload: SignalIn):
    """Receive signal from bot"""
    try:
        db = get_db()
        
        logger.info(f"[signals] ▶ {payload.symbol} {payload.direction} @ {payload.entry} | candles={len(payload.candles)}")
        
        # Serialize complex fields
        pattern_points_json = json.dumps([p.dict() for p in payload.pattern_points]) if payload.pattern_points else None
        candles_json = json.dumps([c.dict() for c in payload.candles]) if payload.candles else None
        breakout_json = json.dumps(payload.breakout_point.dict()) if payload.breakout_point else None

        expires_at = datetime.utcnow() + timedelta(hours=payload.expires_in_hours)
        
        signal_data = {
            "symbol": payload.symbol,
            "direction": payload.direction.upper(),
            "entry": payload.entry,
            "target": payload.target,
            "stop": payload.stop,
            "entry_price": float(payload.entry) if payload.entry else 0.0,
            "take_profit": float(payload.target) if payload.target else 0.0,
            "stop_loss": float(payload.stop) if payload.stop else 0.0,
            "confidence": int(payload.confidence),
            "ai_confidence": int(payload.confidence),
            "asset_type": payload.asset_type,
            "country": payload.country,
            "pattern": payload.pattern,
            "timeframe": payload.timeframe,
            "pattern_points": pattern_points_json,
            "candles": candles_json,
            "breakout_point": breakout_json,
            "is_pattern_idea": payload.is_pattern_idea,
            "pattern_name": payload.pattern_name or "Breakout",
            "expires_at": expires_at
        }
        
        result = await db.create_signal(signal_data)
        signal_id = result.get("id") if result else None
        
        logger.info(f"[signals] ✅ {payload.symbol} saved | id={signal_id}")
        
        return JSONResponse(
            status_code=201,
            content={
                "ok": True,
                "signal_id": signal_id,
                "symbol": payload.symbol,
                "candles_stored": len(payload.candles),
                "pattern": payload.pattern_name or "Breakout"
            }
        )
        
    except Exception as e:
        logger.exception(f"[signals] ❌ Failed to save: {e}")
        return JSONResponse(
            status_code=500, 
            content={"ok": False, "error": str(e)}
        )

@router.get("/signals/enhanced")
async def get_enhanced_signals(limit: int = 50):
    """Get enhanced signals with candles"""
    try:
        db = get_db()
        signals = await db.get_active_signals(limit)
        
        # Convert datetime to ISO strings
        for signal in signals:
            for key in ['created_at', 'expires_at', 'updated_at']:
                if signal.get(key) and isinstance(signal[key], datetime):
                    signal[key] = signal[key].isoformat()
        
        total_candles = sum(len(s.get("candles") or []) for s in signals)
        logger.info(f"[signals] GET /enhanced — {len(signals)} signals, {total_candles} candles")
        
        return signals
        
    except Exception as e:
        logger.exception(f"[signals] GET error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/signals/active")
async def get_active_signals(country: str = "all", asset_type: str = "forex", limit: int = 50):
    """Legacy active signals endpoint"""
    try:
        db = get_db()
        signals = await db.get_active_signals(limit)
        
        # Filter
        if country != "all":
            signals = [s for s in signals if s.get("country") == country]
        if asset_type != "all":
            signals = [s for s in signals if s.get("asset_type") == asset_type]
        
        # Convert datetime
        for signal in signals:
            for key in ['created_at', 'expires_at', 'updated_at']:
                if signal.get(key) and isinstance(signal[key], datetime):
                    signal[key] = signal[key].isoformat()
        
        return signals
        
    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/signals/{signal_id}")
async def get_signal(signal_id: int):
    """Get single signal"""
    try:
        db = get_db()
        signal = await db.get_signal_by_id(signal_id)
        
        if not signal:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        
        # Convert datetime
        for key in ['created_at', 'expires_at', 'updated_at']:
            if signal.get(key) and isinstance(signal[key], datetime):
                signal[key] = signal[key].isoformat()
        
        return signal
        
    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: int):
    """Soft delete signal"""
    try:
        db = get_db()
        query = "UPDATE signals SET status = 'inactive' WHERE id = $1 RETURNING id"
        result = await db.fetch_one(query, {"id": signal_id})
        
        if not result:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        
        return {"id": signal_id, "status": "deleted"}
        
    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/signals/expire-old")
async def expire_old_signals():
    """Expire old signals"""
    try:
        db = get_db()
        count = await db.expire_old_signals()
        logger.info(f"[signals] Expired {count} old signals")
        return {"expired_count": count}
    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
