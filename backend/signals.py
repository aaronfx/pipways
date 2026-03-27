# signals.py — Enhanced Signals API with Pattern Coordinates
# Deploy to: backend/signals.py

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from backend.database import database, signals
from backend.auth import get_current_user
import json

router = APIRouter(tags=["signals"])


# ═══════════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class PatternPoint(BaseModel):
    """Single point in a pattern (time + price)"""
    time: int  # Unix timestamp
    price: float


class PatternLine(BaseModel):
    """A line connecting two points"""
    start: PatternPoint
    end: PatternPoint


class SignalCreate(BaseModel):
    symbol: str
    direction: str  # BUY or SELL
    entry: str
    target: str
    stop: str
    timeframe: str = "4H"
    pattern: Optional[str] = None
    pattern_points: Optional[List[Dict[str, Any]]] = None  # Array of {time, price} pairs
    pattern_lines: Optional[List[Dict[str, Any]]] = None   # Array of line definitions
    confidence: int = 75
    technical_summary: Optional[str] = None
    is_pattern_idea: bool = False
    expires_at: Optional[datetime] = None


class SignalResponse(BaseModel):
    id: int
    symbol: str
    direction: str
    entry: str
    target: str
    stop: str
    timeframe: str
    pattern: Optional[str]
    pattern_points: Optional[List[Dict[str, Any]]]
    pattern_lines: Optional[List[Dict[str, Any]]]
    confidence: int
    technical_summary: Optional[str]
    is_pattern_idea: bool
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    full_name: Optional[str] = None


class CandleData(BaseModel):
    """OHLC candle data"""
    time: int  # Unix timestamp
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
# SYMBOL METADATA
# ═══════════════════════════════════════════════════════════════════════════════

SYMBOL_INFO = {
    "EURUSD": {"name": "Euro vs US Dollar", "type": "forex", "digits": 5},
    "GBPUSD": {"name": "British Pound vs US Dollar", "type": "forex", "digits": 5},
    "USDJPY": {"name": "US Dollar vs Japanese Yen", "type": "forex", "digits": 3},
    "AUDUSD": {"name": "Australian Dollar vs US Dollar", "type": "forex", "digits": 5},
    "NZDUSD": {"name": "New Zealand Dollar vs US Dollar", "type": "forex", "digits": 5},
    "AUDCAD": {"name": "Australian Dollar vs Canadian Dollar", "type": "forex", "digits": 5},
    "GBPJPY": {"name": "British Pound vs Japanese Yen", "type": "forex", "digits": 3},
    "EURJPY": {"name": "Euro vs Japanese Yen", "type": "forex", "digits": 3},
    "XAUUSD": {"name": "Gold vs US Dollar", "type": "commodity", "digits": 2},
    "XAGUSD": {"name": "Silver vs US Dollar", "type": "commodity", "digits": 3},
    "US30": {"name": "Dow Jones Industrial Average", "type": "indices", "digits": 0},
    "GER40": {"name": "Germany 40 Index", "type": "indices", "digits": 0},
    "CHINA50": {"name": "China A50 Index", "type": "indices", "digits": 0},
    "BTCUSD": {"name": "Bitcoin vs US Dollar", "type": "crypto", "digits": 2},
    "ETHUSD": {"name": "Ethereum vs US Dollar", "type": "crypto", "digits": 2},
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE MIGRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def run_signals_migration():
    """Add missing columns to signals table"""
    _COLUMN_MIGRATIONS = [
        ("pattern", "VARCHAR(100)"),
        ("confidence", "INTEGER DEFAULT 75"),
        ("timeframe", "VARCHAR(10) DEFAULT '4H'"),
        ("technical_summary", "TEXT"),
        ("volatility_index", "FLOAT"),
        ("is_pattern_idea", "BOOLEAN DEFAULT FALSE"),
        ("is_published", "BOOLEAN DEFAULT TRUE"),
        ("expires_at", "TIMESTAMP"),
        ("pattern_points", "TEXT"),  # JSON array of {time, price}
        ("pattern_lines", "TEXT"),   # JSON array of line definitions
    ]

    for col_name, col_type in _COLUMN_MIGRATIONS:
        try:
            await database.execute(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}")
            print(f"[Signals] Added column: {col_name}")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                pass
            else:
                print(f"[Signals] Column {col_name} migration note: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CANDLES ENDPOINT (FOR CHART DATAFEED)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/candles")
async def get_candles(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1H", description="Timeframe: 1M, 5M, 15M, 1H, 4H, 1D"),
    from_ts: Optional[int] = Query(None, description="Start timestamp (unix)"),
    to_ts: Optional[int] = Query(None, description="End timestamp (unix)"),
    limit: int = Query(500, description="Number of candles"),
    _user: dict = Depends(get_current_user)
):
    """
    Get OHLC candle data for charting.
    
    This endpoint is designed to be connected to a real data source:
    - MT5 bridge
    - TwelveData API
    - Binance API
    - EODHD API
    
    For now, returns placeholder structure that frontend can handle.
    """
    
    # TODO: Replace with real data source integration
    # Example integrations:
    #
    # MT5:
    #   from mt5_bridge import get_rates
    #   candles = get_rates(symbol, timeframe, limit)
    #
    # TwelveData:
    #   response = httpx.get(f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={timeframe}")
    #   candles = parse_twelvedata(response.json())
    #
    # Binance:
    #   response = httpx.get(f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}")
    #   candles = parse_binance(response.json())
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": [],  # Empty = frontend will use TradingView widget fallback
        "source": "pending_integration",
        "message": "Connect MT5/API for real data"
    }


@router.get("/symbol-info/{symbol}")
async def get_symbol_info(
    symbol: str,
    _user: dict = Depends(get_current_user)
):
    """Get symbol metadata for charting"""
    info = SYMBOL_INFO.get(symbol, {
        "name": symbol,
        "type": "forex",
        "digits": 5
    })
    return {
        "symbol": symbol,
        **info,
        "exchange": "FOREX" if info.get("type") == "forex" else "INDEX",
        "timezone": "Etc/UTC"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/enhanced")
async def get_enhanced_signals(
    status: str = "active",
    _user: dict = Depends(get_current_user)
) -> List[dict]:
    """Get all enhanced signals with pattern data"""
    
    query = signals.select().where(signals.c.status == status)
    rows = await database.fetch_all(query)
    
    result = []
    for row in rows:
        row_dict = dict(row._mapping)
        
        # Parse JSON fields
        if row_dict.get("pattern_points"):
            try:
                row_dict["pattern_points"] = json.loads(row_dict["pattern_points"])
            except:
                row_dict["pattern_points"] = None
                
        if row_dict.get("pattern_lines"):
            try:
                row_dict["pattern_lines"] = json.loads(row_dict["pattern_lines"])
            except:
                row_dict["pattern_lines"] = None
        
        # Add full name
        symbol = row_dict.get("symbol", "")
        info = SYMBOL_INFO.get(symbol, {})
        row_dict["full_name"] = info.get("name", symbol)
        row_dict["asset_type"] = info.get("type", "forex")
        row_dict["digits"] = info.get("digits", 5)
        
        result.append(row_dict)
    
    return result


@router.get("/{signal_id}")
async def get_signal(
    signal_id: int,
    _user: dict = Depends(get_current_user)
) -> dict:
    """Get single signal with full details"""
    
    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    row_dict = dict(row._mapping)
    
    # Parse JSON fields
    if row_dict.get("pattern_points"):
        try:
            row_dict["pattern_points"] = json.loads(row_dict["pattern_points"])
        except:
            row_dict["pattern_points"] = None
            
    if row_dict.get("pattern_lines"):
        try:
            row_dict["pattern_lines"] = json.loads(row_dict["pattern_lines"])
        except:
            row_dict["pattern_lines"] = None
    
    # Add metadata
    symbol = row_dict.get("symbol", "")
    info = SYMBOL_INFO.get(symbol, {})
    row_dict["full_name"] = info.get("name", symbol)
    row_dict["asset_type"] = info.get("type", "forex")
    row_dict["digits"] = info.get("digits", 5)
    
    return row_dict


@router.post("/")
async def create_signal(
    signal: SignalCreate,
    _user: dict = Depends(get_current_user)
) -> dict:
    """Create a new signal with pattern coordinates"""
    
    # Serialize JSON fields
    pattern_points_json = json.dumps(signal.pattern_points) if signal.pattern_points else None
    pattern_lines_json = json.dumps(signal.pattern_lines) if signal.pattern_lines else None
    
    # Default expiry if not set
    expires_at = signal.expires_at or (datetime.utcnow() + timedelta(days=2))
    
    query = signals.insert().values(
        symbol=signal.symbol,
        direction=signal.direction,
        entry=signal.entry,
        target=signal.target,
        stop=signal.stop,
        timeframe=signal.timeframe,
        pattern=signal.pattern,
        pattern_points=pattern_points_json,
        pattern_lines=pattern_lines_json,
        confidence=signal.confidence,
        technical_summary=signal.technical_summary,
        is_pattern_idea=signal.is_pattern_idea,
        is_published=True,
        status="active",
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    signal_id = await database.execute(query)
    
    return {"id": signal_id, "status": "created"}


@router.put("/{signal_id}")
async def update_signal(
    signal_id: int,
    updates: dict,
    _user: dict = Depends(get_current_user)
) -> dict:
    """Update signal fields"""
    
    # Handle JSON fields
    if "pattern_points" in updates and updates["pattern_points"] is not None:
        updates["pattern_points"] = json.dumps(updates["pattern_points"])
    if "pattern_lines" in updates and updates["pattern_lines"] is not None:
        updates["pattern_lines"] = json.dumps(updates["pattern_lines"])
    
    query = signals.update().where(signals.c.id == signal_id).values(**updates)
    await database.execute(query)
    
    return {"id": signal_id, "status": "updated"}


@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    _user: dict = Depends(get_current_user)
) -> dict:
    """Delete a signal"""
    
    query = signals.delete().where(signals.c.id == signal_id)
    await database.execute(query)
    
    return {"id": signal_id, "status": "deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# SAMPLE DATA SEEDING
# ═══════════════════════════════════════════════════════════════════════════════

async def seed_enhanced_signals():
    """Seed sample signals with pattern coordinates"""
    
    # Check if signals exist
    count = await database.fetch_val("SELECT COUNT(*) FROM signals WHERE status = 'active'")
    if count and count > 0:
        print(f"[Signals] {count} active signals exist, skipping seed")
        return
    
    now = datetime.utcnow()
    base_time = int(now.timestamp())
    hour = 3600
    
    sample_signals = [
        # ═══ AI-DRIVEN SIGNALS ═══
        {
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry": "1.08250",
            "target": "1.08850",
            "stop": "1.07850",
            "timeframe": "4H",
            "pattern": "BREAKOUT",
            "confidence": 82,
            "is_pattern_idea": False,
            "technical_summary": "Strong bullish momentum with breakout above key resistance",
            "pattern_lines": [
                {"start": {"time": base_time - 48*hour, "price": 1.0810}, "end": {"time": base_time, "price": 1.0810}}
            ],
            "expires_at": now + timedelta(hours=48)
        },
        {
            "symbol": "GBPUSD",
            "direction": "BUY",
            "entry": "1.29450",
            "target": "1.30150",
            "stop": "1.28950",
            "timeframe": "1H",
            "pattern": "SUPPORT",
            "confidence": 78,
            "is_pattern_idea": False,
            "technical_summary": "Price bouncing from strong support zone",
            "pattern_lines": [
                {"start": {"time": base_time - 24*hour, "price": 1.2940}, "end": {"time": base_time, "price": 1.2940}}
            ],
            "expires_at": now + timedelta(hours=24)
        },
        {
            "symbol": "XAUUSD",
            "direction": "BUY",
            "entry": "2345.50",
            "target": "2385.00",
            "stop": "2320.00",
            "timeframe": "4H",
            "pattern": "SUPPORT",
            "confidence": 85,
            "is_pattern_idea": False,
            "technical_summary": "Gold finding support at key psychological level",
            "pattern_lines": [
                {"start": {"time": base_time - 72*hour, "price": 2340}, "end": {"time": base_time, "price": 2340}}
            ],
            "expires_at": now + timedelta(hours=48)
        },
        {
            "symbol": "BTCUSD",
            "direction": "BUY",
            "entry": "67500",
            "target": "72000",
            "stop": "64500",
            "timeframe": "4H",
            "pattern": "BREAKOUT",
            "confidence": 80,
            "is_pattern_idea": False,
            "technical_summary": "Bitcoin breaking above consolidation range",
            "pattern_lines": [
                {"start": {"time": base_time - 96*hour, "price": 67000}, "end": {"time": base_time, "price": 67000}}
            ],
            "expires_at": now + timedelta(hours=72)
        },
        {
            "symbol": "US30",
            "direction": "BUY",
            "entry": "38950",
            "target": "39250",
            "stop": "38700",
            "timeframe": "1H",
            "pattern": "BREAKOUT",
            "confidence": 76,
            "is_pattern_idea": False,
            "technical_summary": "Dow Jones showing bullish continuation",
            "pattern_lines": [
                {"start": {"time": base_time - 24*hour, "price": 38900}, "end": {"time": base_time, "price": 38900}}
            ],
            "expires_at": now + timedelta(hours=24)
        },
        {
            "symbol": "USDJPY",
            "direction": "SELL",
            "entry": "154.850",
            "target": "153.500",
            "stop": "155.600",
            "timeframe": "4H",
            "pattern": "REVERSAL",
            "confidence": 74,
            "is_pattern_idea": False,
            "technical_summary": "Bearish reversal at resistance",
            "pattern_lines": [
                {"start": {"time": base_time - 48*hour, "price": 155.0}, "end": {"time": base_time, "price": 155.0}}
            ],
            "expires_at": now + timedelta(hours=48)
        },
        {
            "symbol": "AUDUSD",
            "direction": "BUY",
            "entry": "0.65280",
            "target": "0.66000",
            "stop": "0.64800",
            "timeframe": "4H",
            "pattern": "SUPPORT",
            "confidence": 77,
            "is_pattern_idea": False,
            "technical_summary": "Aussie bouncing from demand zone",
            "pattern_lines": [
                {"start": {"time": base_time - 48*hour, "price": 0.6520}, "end": {"time": base_time, "price": 0.6520}}
            ],
            "expires_at": now + timedelta(hours=48)
        },
        
        # ═══ PATTERN TRADE IDEAS (AnalysisIQ) ═══
        {
            "symbol": "NZDUSD",
            "direction": "BUY",
            "entry": "0.61250",
            "target": "0.61750",
            "stop": "0.60900",
            "timeframe": "4H",
            "pattern": "FLAG",
            "confidence": 79,
            "is_pattern_idea": True,
            "technical_summary": "Bullish flag forming after strong impulse move",
            "pattern_lines": [
                {"start": {"time": base_time - 36*hour, "price": 0.6140}, "end": {"time": base_time - 6*hour, "price": 0.6120}},
                {"start": {"time": base_time - 36*hour, "price": 0.6115}, "end": {"time": base_time - 6*hour, "price": 0.6095}}
            ],
            "expires_at": now + timedelta(hours=24)
        },
        {
            "symbol": "AUDCAD",
            "direction": "BUY",
            "entry": "0.95426",
            "target": "0.95800",
            "stop": "0.95200",
            "timeframe": "1H",
            "pattern": "FLAG",
            "confidence": 75,
            "is_pattern_idea": True,
            "technical_summary": "Continuation flag pattern",
            "pattern_lines": [
                {"start": {"time": base_time - 24*hour, "price": 0.9550}, "end": {"time": base_time - 4*hour, "price": 0.9535}},
                {"start": {"time": base_time - 24*hour, "price": 0.9530}, "end": {"time": base_time - 4*hour, "price": 0.9515}}
            ],
            "expires_at": now + timedelta(hours=72)
        },
        {
            "symbol": "GBPJPY",
            "direction": "BUY",
            "entry": "189.450",
            "target": "190.450",
            "stop": "188.750",
            "timeframe": "1H",
            "pattern": "WEDGE",
            "confidence": 81,
            "is_pattern_idea": True,
            "technical_summary": "Falling wedge breakout imminent",
            "pattern_lines": [
                {"start": {"time": base_time - 48*hour, "price": 190.5}, "end": {"time": base_time - 4*hour, "price": 189.8}},
                {"start": {"time": base_time - 48*hour, "price": 188.5}, "end": {"time": base_time - 4*hour, "price": 189.2}}
            ],
            "expires_at": now + timedelta(hours=48)
        },
        {
            "symbol": "EURSEEK",
            "direction": "SELL",
            "entry": "10.8830",
            "target": "10.8400",
            "stop": "10.9100",
            "timeframe": "4H",
            "pattern": "WEDGE",
            "confidence": 73,
            "is_pattern_idea": True,
            "technical_summary": "Rising wedge reversal pattern",
            "pattern_lines": [
                {"start": {"time": base_time - 72*hour, "price": 10.82}, "end": {"time": base_time - 4*hour, "price": 10.90}},
                {"start": {"time": base_time - 72*hour, "price": 10.78}, "end": {"time": base_time - 4*hour, "price": 10.86}}
            ],
            "expires_at": now + timedelta(hours=48)
        },
        {
            "symbol": "CHINA50",
            "direction": "BUY",
            "entry": "14495",
            "target": "14650",
            "stop": "14380",
            "timeframe": "1H",
            "pattern": "PENNANT",
            "confidence": 77,
            "is_pattern_idea": True,
            "technical_summary": "Bullish pennant continuation",
            "pattern_lines": [
                {"start": {"time": base_time - 24*hour, "price": 14550}, "end": {"time": base_time - 2*hour, "price": 14500}},
                {"start": {"time": base_time - 24*hour, "price": 14420}, "end": {"time": base_time - 2*hour, "price": 14480}}
            ],
            "expires_at": now + timedelta(hours=72)
        },
        {
            "symbol": "XAGUSD",
            "direction": "BUY",
            "entry": "27.850",
            "target": "28.450",
            "stop": "27.450",
            "timeframe": "4H",
            "pattern": "SYMMETRICAL_TRIANGLE",
            "confidence": 83,
            "is_pattern_idea": True,
            "technical_summary": "Silver forming symmetrical triangle near apex",
            "pattern_lines": [
                {"start": {"time": base_time - 96*hour, "price": 28.50}, "end": {"time": base_time - 4*hour, "price": 27.90}},
                {"start": {"time": base_time - 96*hour, "price": 27.20}, "end": {"time": base_time - 4*hour, "price": 27.75}}
            ],
            "expires_at": now + timedelta(hours=48)
        },
        {
            "symbol": "ETHUSD",
            "direction": "BUY",
            "entry": "3450",
            "target": "3650",
            "stop": "3300",
            "timeframe": "4H",
            "pattern": "DOUBLE_BOTTOM",
            "confidence": 80,
            "is_pattern_idea": True,
            "technical_summary": "Double bottom reversal pattern",
            "pattern_points": [
                {"time": base_time - 72*hour, "price": 3320},
                {"time": base_time - 24*hour, "price": 3325}
            ],
            "pattern_lines": [
                {"start": {"time": base_time - 72*hour, "price": 3320}, "end": {"time": base_time - 24*hour, "price": 3325}}
            ],
            "expires_at": now + timedelta(hours=72)
        },
        {
            "symbol": "GER40",
            "direction": "SELL",
            "entry": "18250",
            "target": "18050",
            "stop": "18400",
            "timeframe": "1H",
            "pattern": "DOUBLE_TOP",
            "confidence": 76,
            "is_pattern_idea": True,
            "technical_summary": "Double top reversal at resistance",
            "pattern_points": [
                {"time": base_time - 48*hour, "price": 18380},
                {"time": base_time - 12*hour, "price": 18375}
            ],
            "pattern_lines": [
                {"start": {"time": base_time - 48*hour, "price": 18380}, "end": {"time": base_time - 12*hour, "price": 18375}}
            ],
            "expires_at": now + timedelta(hours=36)
        },
    ]
    
    for sig in sample_signals:
        # Serialize JSON fields
        if sig.get("pattern_points"):
            sig["pattern_points"] = json.dumps(sig["pattern_points"])
        if sig.get("pattern_lines"):
            sig["pattern_lines"] = json.dumps(sig["pattern_lines"])
        
        sig["status"] = "active"
        sig["is_published"] = True
        sig["created_at"] = now
        
        try:
            query = signals.insert().values(**sig)
            await database.execute(query)
        except Exception as e:
            print(f"[Signals] Seed error: {e}")
    
    print(f"[Signals] Seeded {len(sample_signals)} enhanced signals")
