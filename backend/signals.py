# Signals API — Production Clean Version
# Deploy to: routes/signals.py
#
# ✅ ONLY returns real database records
# ✅ NO mock/fake/placeholder data
# ✅ NO seed data injection
# ✅ Bot writes → DB → API reads → Frontend displays

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

router = APIRouter(prefix="/signals", tags=["signals"])

# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class SignalCreate(BaseModel):
    symbol: str
    direction: str  # BUY or SELL
    entry: str
    target: str
    stop: str
    pattern: Optional[str] = None
    timeframe: Optional[str] = "4H"
    confidence: Optional[int] = 75
    asset_type: Optional[str] = "forex"
    country: Optional[str] = "all"
    is_pattern_idea: Optional[bool] = False
    full_name: Optional[str] = None
    technical_summary: Optional[str] = None
    pattern_points: Optional[str] = None  # JSON string
    pattern_lines: Optional[str] = None   # JSON string

class SignalUpdate(BaseModel):
    symbol: Optional[str] = None
    direction: Optional[str] = None
    entry: Optional[str] = None
    target: Optional[str] = None
    stop: Optional[str] = None
    pattern: Optional[str] = None
    timeframe: Optional[str] = None
    confidence: Optional[int] = None
    status: Optional[str] = None
    is_pattern_idea: Optional[bool] = None

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_database():
    """Get database connection from main app"""
    from backend.database import database
    return database

# ═══════════════════════════════════════════════════════════════════════════════
# MIGRATION — Run on startup to ensure columns exist
# ═══════════════════════════════════════════════════════════════════════════════

async def run_signals_migration():
    """Add missing columns to signals table"""
    db = get_database()
    
    columns_to_add = [
        ("full_name", "VARCHAR(255)"),
        ("ai_confidence", "INTEGER"),
        ("sentiment_bullish", "INTEGER"),
        ("sentiment_bearish", "INTEGER"),
        ("is_pattern_idea", "BOOLEAN DEFAULT FALSE"),
        ("technical_summary", "TEXT"),
        ("volatility_index", "FLOAT"),
        ("pattern_points", "TEXT"),
        ("pattern_lines", "TEXT"),
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            check_sql = f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'signals' AND column_name = '{col_name}'
            """
            result = await db.fetch_one(check_sql)
            
            if not result:
                alter_sql = f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}"
                await db.execute(alter_sql)
                print(f"[SIGNALS] ✅ Added column: {col_name}")
        except Exception as e:
            print(f"[SIGNALS] ⚠️ Column {col_name}: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS — REAL DATA ONLY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/enhanced")
async def get_enhanced_signals():
    """
    GET /signals/enhanced
    
    Returns ALL active signals from the database.
    NO fake data. NO fallbacks. ONLY real bot signals.
    """
    db = get_database()
    
    try:
        # Query ONLY real database records
        query = """
            SELECT * FROM signals 
            WHERE status = 'active' 
            ORDER BY created_at DESC
        """
        rows = await db.fetch_all(query)
        
        if not rows:
            print("[SIGNALS] ℹ️ No active signals in database")
            return []  # Return empty array, NOT fake data
        
        # Convert rows to dicts
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
            
            signals.append(signal)
        
        print(f"[SIGNALS] ✅ Returning {len(signals)} real signals")
        return signals
        
    except Exception as e:
        print(f"[SIGNALS] ❌ Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_signals(
    country: str = "all",
    asset_type: str = "forex"
):
    """
    GET /signals/active
    
    Returns filtered active signals. Now has default params to avoid 422 errors.
    """
    db = get_database()
    
    try:
        # Build query with optional filters
        query = "SELECT * FROM signals WHERE status = 'active'"
        params = {}
        
        if country and country != "all":
            query += " AND country = :country"
            params["country"] = country
            
        if asset_type and asset_type != "all":
            query += " AND asset_type = :asset_type"
            params["asset_type"] = asset_type
        
        query += " ORDER BY created_at DESC"
        
        rows = await db.fetch_all(query, params)
        
        signals = [dict(row) for row in rows] if rows else []
        print(f"[SIGNALS] ✅ /active returning {len(signals)} signals (country={country}, asset={asset_type})")
        return signals
        
    except Exception as e:
        print(f"[SIGNALS] ❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{signal_id}")
async def get_signal(signal_id: int):
    """
    GET /signals/{id}
    
    Returns a single signal by ID.
    """
    db = get_database()
    
    try:
        query = "SELECT * FROM signals WHERE id = :signal_id"
        row = await db.fetch_one(query, {"signal_id": signal_id})
        
        if not row:
            raise HTTPException(status_code=404, detail="Signal not found")
        
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
        
        return signal
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SIGNALS] ❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_signal(signal: SignalCreate):
    """
    POST /signals/
    
    Creates a new signal. Used by the trading bot.
    """
    db = get_database()
    
    try:
        # Prepare pattern data as JSON strings
        pattern_points_json = signal.pattern_points if signal.pattern_points else None
        pattern_lines_json = signal.pattern_lines if signal.pattern_lines else None
        
        query = """
            INSERT INTO signals (
                symbol, direction, entry, target, stop,
                pattern, timeframe, confidence, ai_confidence,
                asset_type, country, is_pattern_idea, full_name,
                technical_summary, pattern_points, pattern_lines,
                status, is_published, created_at, expires_at
            ) VALUES (
                :symbol, :direction, :entry, :target, :stop,
                :pattern, :timeframe, :confidence, :confidence,
                :asset_type, :country, :is_pattern_idea, :full_name,
                :technical_summary, :pattern_points, :pattern_lines,
                'active', TRUE, NOW(), NOW() + INTERVAL '24 hours'
            )
            RETURNING id
        """
        
        params = {
            "symbol": signal.symbol,
            "direction": signal.direction.upper(),
            "entry": signal.entry,
            "target": signal.target,
            "stop": signal.stop,
            "pattern": signal.pattern or "BREAKOUT",
            "timeframe": signal.timeframe or "4H",
            "confidence": signal.confidence or 75,
            "asset_type": signal.asset_type or "forex",
            "country": signal.country or "all",
            "is_pattern_idea": signal.is_pattern_idea or False,
            "full_name": signal.full_name,
            "technical_summary": signal.technical_summary,
            "pattern_points": pattern_points_json,
            "pattern_lines": pattern_lines_json,
        }
        
        result = await db.fetch_one(query, params)
        signal_id = result["id"] if result else None
        
        print(f"[SIGNALS] ✅ Created signal #{signal_id}: {signal.symbol} {signal.direction}")
        
        return {"id": signal_id, "status": "created", "symbol": signal.symbol}
        
    except Exception as e:
        print(f"[SIGNALS] ❌ Error creating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{signal_id}")
async def update_signal(signal_id: int, signal: SignalUpdate):
    """
    PUT /signals/{id}
    
    Updates an existing signal.
    """
    db = get_database()
    
    try:
        # Build dynamic update query
        updates = []
        params = {"signal_id": signal_id}
        
        if signal.symbol is not None:
            updates.append("symbol = :symbol")
            params["symbol"] = signal.symbol
        if signal.direction is not None:
            updates.append("direction = :direction")
            params["direction"] = signal.direction.upper()
        if signal.entry is not None:
            updates.append("entry = :entry")
            params["entry"] = signal.entry
        if signal.target is not None:
            updates.append("target = :target")
            params["target"] = signal.target
        if signal.stop is not None:
            updates.append("stop = :stop")
            params["stop"] = signal.stop
        if signal.pattern is not None:
            updates.append("pattern = :pattern")
            params["pattern"] = signal.pattern
        if signal.timeframe is not None:
            updates.append("timeframe = :timeframe")
            params["timeframe"] = signal.timeframe
        if signal.confidence is not None:
            updates.append("confidence = :confidence")
            updates.append("ai_confidence = :confidence")
            params["confidence"] = signal.confidence
        if signal.status is not None:
            updates.append("status = :status")
            params["status"] = signal.status
        if signal.is_pattern_idea is not None:
            updates.append("is_pattern_idea = :is_pattern_idea")
            params["is_pattern_idea"] = signal.is_pattern_idea
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        query = f"UPDATE signals SET {', '.join(updates)} WHERE id = :signal_id RETURNING id"
        result = await db.fetch_one(query, params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        print(f"[SIGNALS] ✅ Updated signal #{signal_id}")
        return {"id": signal_id, "status": "updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SIGNALS] ❌ Error updating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{signal_id}")
async def delete_signal(signal_id: int):
    """
    DELETE /signals/{id}
    
    Deletes a signal (or marks as inactive).
    """
    db = get_database()
    
    try:
        # Soft delete - mark as inactive
        query = "UPDATE signals SET status = 'inactive' WHERE id = :signal_id RETURNING id"
        result = await db.fetch_one(query, {"signal_id": signal_id})
        
        if not result:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        print(f"[SIGNALS] ✅ Deleted signal #{signal_id}")
        return {"id": signal_id, "status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SIGNALS] ❌ Error deleting signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expire-old")
async def expire_old_signals():
    """
    POST /signals/expire-old
    
    Marks expired signals as inactive. Can be called by cron job.
    """
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
        
        print(f"[SIGNALS] ✅ Expired {count} old signals")
        return {"expired_count": count}
        
    except Exception as e:
        print(f"[SIGNALS] ❌ Error expiring signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
