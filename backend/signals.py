# signals.py  —  Pipways backend route for GreenXTrades signal ingestion
# Deploy to: backend/signals.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(redirect_slashes=False, tags=["signals"])

def get_database():
    """Get database connection from main app"""
    from backend.database import database
    return database

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
    candles: List[CandleData] = Field(default_factory=list)  # 🔥 REAL CANDLES
    is_pattern_idea: bool = False
    bias_d1: Optional[str] = None
    bias_h4: Optional[str] = None
    bos_m5: Optional[str] = None
    test_signal: Optional[bool] = False

    class Config:
        extra = "allow"

@router.post("/signals")
async def create_signal(payload: SignalIn):
    """Receive signal from bot and save to DB with candles"""
    db = get_database()
    
    try:
        logger.info(f"[signals] ▶ {payload.symbol} {payload.direction} @ {payload.entry} | candles={len(payload.candles)}")

        # Convert to JSON strings
        pattern_points_json = json.dumps([p.dict() for p in payload.pattern_points]) if payload.pattern_points else None
        candles_json = json.dumps([c.dict() for c in payload.candles]) if payload.candles else None
        
        if candles_json:
            logger.info(f"[signals] 📊 Storing {len(payload.candles)} candles")

        conf_int = int(payload.confidence)
        expires_hours = int(payload.expires_in_hours)
        
        entry_price = float(payload.entry) if payload.entry else 0.0
        take_profit = float(payload.target) if payload.target else 0.0
        stop_loss = float(payload.stop) if payload.stop else 0.0

        query = """
            INSERT INTO signals (
                symbol, direction, entry, target, stop,
                entry_price, take_profit, stop_loss,
                confidence, ai_confidence, asset_type, country,
                pattern, timeframe, is_pattern_idea,
                pattern_points, candles, status, is_published,
                created_at, expires_at
            ) VALUES (
                :symbol, :direction, :entry, :target, :stop,
                :entry_price, :take_profit, :stop_loss,
                :confidence, :ai_confidence, :asset_type, :country,
                :pattern, :timeframe, :is_pattern_idea,
                :pattern_points, :candles, 'active', TRUE,
                NOW(), NOW() + INTERVAL '%s hours'
            )
            RETURNING id
        """ % expires_hours

        params = {
            "symbol": payload.symbol,
            "direction": payload.direction.upper(),
            "entry": payload.entry,
            "target": payload.target,
            "stop": payload.stop,
            "entry_price": entry_price,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "confidence": conf_int,
            "ai_confidence": conf_int,
            "asset_type": payload.asset_type,
            "country": payload.country,
            "pattern": payload.pattern,
            "timeframe": payload.timeframe,
            "is_pattern_idea": payload.is_pattern_idea,
            "pattern_points": pattern_points_json,
            "candles": candles_json,
        }

        result = await db.fetch_one(query, params)
        signal_id = result["id"] if result else None

        logger.info(f"[signals] ✅ {payload.symbol} saved | id={signal_id}")

        return JSONResponse(
            status_code=201,
            content={
                "ok": True,
                "signal_id": signal_id,
                "symbol": payload.symbol,
                "candles_stored": len(payload.candles),
            },
        )

    except Exception as e:
        logger.exception(f"[signals] ❌ Failed to save: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@router.get("/signals/enhanced")
async def get_enhanced_signals(limit: int = 50):
    """Return active signals WITH CANDLES for dashboard"""
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
            return []
        
        signals = []
        for row in rows:
            signal = dict(row)
            
            # Parse pattern_points
            if signal.get('pattern_points'):
                try:
                    signal['pattern_points'] = json.loads(signal['pattern_points'])
                except:
                    signal['pattern_points'] = None
            
            # 🔥 CRITICAL: Parse candles back to array
            if signal.get('candles'):
                try:
                    parsed = json.loads(signal['candles'])
                    if isinstance(parsed, list) and len(parsed) > 0:
                        signal['candles'] = parsed
                        logger.debug(f"[signals] 📊 Returning {len(parsed)} candles for {signal['symbol']}")
                    else:
                        signal['candles'] = None
                except Exception as e:
                    logger.warning(f"[signals] Failed to parse candles: {e}")
                    signal['candles'] = None
            else:
                signal['candles'] = None
            
            # Convert datetime to ISO string
            for key in ['created_at', 'expires_at', 'updated_at']:
                if signal.get(key) and hasattr(signal[key], 'isoformat'):
                    signal[key] = signal[key].isoformat()
            
            signals.append(signal)
        
        total = sum(len(s.get('candles') or []) for s in signals)
        logger.info(f"[signals] GET /enhanced — {len(signals)} signals, {total} candles")
        return signals

    except Exception as e:
        logger.exception(f"[signals] GET error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/signals/active")
async def get_active_signals(country: str = "all", asset_type: str = "forex", limit: int = 50):
    """Legacy endpoint - also returns candles"""
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
        signals = []
        
        for row in rows:
            signal = dict(row)
            
            # Parse candles
            if signal.get('candles'):
                try:
                    signal['candles'] = json.loads(signal['candles'])
                except:
                    signal['candles'] = None
                    
            for key in ['created_at', 'expires_at', 'updated_at']:
                if signal.get(key) and hasattr(signal[key], 'isoformat'):
                    signal[key] = signal[key].isoformat()
            
            signals.append(signal)
        
        return signals

    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/signals/{signal_id}")
async def get_signal(signal_id: int):
    """Get single signal by ID"""
    db = get_database()
    
    try:
        row = await db.fetch_one("SELECT * FROM signals WHERE id = :id", {"id": signal_id})
        
        if not row:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        
        signal = dict(row)
        
        if signal.get('pattern_points'):
            try:
                signal['pattern_points'] = json.loads(signal['pattern_points'])
            except:
                pass
        
        if signal.get('candles'):
            try:
                signal['candles'] = json.loads(signal['candles'])
            except:
                signal['candles'] = None
        
        for key in ['created_at', 'expires_at', 'updated_at']:
            if signal.get(key) and hasattr(signal[key], 'isoformat'):
                signal[key] = signal[key].isoformat()
        
        return signal

    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: int):
    """Soft delete"""
    db = get_database()
    
    try:
        result = await db.fetch_one(
            "UPDATE signals SET status = 'inactive' WHERE id = :id RETURNING id",
            {"id": signal_id}
        )
        
        if not result:
            return JSONResponse(status_code=404, content={"error": "Not found"})
        
        return {"id": signal_id, "status": "deleted"}

    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/signals/expire-old")
async def expire_old_signals():
    """Mark expired as inactive"""
    db = get_database()
    
    try:
        rows = await db.fetch_all(
            "UPDATE signals SET status = 'expired' WHERE status = 'active' AND expires_at < NOW() RETURNING id"
        )
        count = len(rows) if rows else 0
        logger.info(f"[signals] Expired {count} old signals")
        return {"expired_count": count}

    except Exception as e:
        logger.exception(f"[signals] error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
