"""
Enhanced Signals API - Rewritten for databases library pattern
Compatible with Pipways FastAPI + databases stack
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import random

from .database import database, signals, users
from .auth import get_current_user

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════════════════════

class SignalResponse(BaseModel):
    id: int
    symbol: str
    full_name: Optional[str] = None
    direction: str
    pattern: Optional[str] = None
    timeframe: str
    entry: str
    target: str
    stop: str
    current_price: Optional[str] = None
    price_change: Optional[str] = None
    price_change_percent: Optional[str] = None
    sentiment_bearish: int = 50
    sentiment_bullish: int = 50
    confidence: int
    expiry: Optional[str] = None
    expires_at: Optional[datetime] = None
    asset_type: str = "forex"
    country: str = "all"
    chart_data: Optional[dict] = None
    created_at: datetime
    status: str = "active"
    ai_confidence: Optional[int] = None

    class Config:
        from_attributes = True


class SignalCreateRequest(BaseModel):
    symbol: str
    full_name: Optional[str] = None
    direction: str
    pattern: Optional[str] = None
    timeframe: str = "1H"
    entry: str
    target: str
    stop: str
    confidence: int = 75
    asset_type: str = "forex"
    country: str = "all"
    sentiment_bearish: int = 50
    sentiment_bullish: int = 50
    expires_in_hours: int = 24


class ChartAnalysisResponse(BaseModel):
    signal: SignalResponse
    analysis: dict
    chart_levels: dict
    ohlc_data: Optional[list] = None


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_full_name_from_symbol(symbol: str) -> str:
    """Convert symbol to full name"""
    symbol_names = {
        "AUDCAD": "Australian Dollar vs Canadian Dollar",
        "EURUSD": "Euro vs US Dollar",
        "GBPUSD": "British Pound vs US Dollar",
        "USDJPY": "US Dollar vs Japanese Yen",
        "GBPJPY": "British Pound vs Japanese Yen",
        "EURAUD": "Euro vs Australian Dollar",
        "AUDNZD": "Australian Dollar vs New Zealand Dollar",
        "EURGBP": "Euro vs British Pound",
        "USDCAD": "US Dollar vs Canadian Dollar",
        "USDCHF": "US Dollar vs Swiss Franc",
        "NZDUSD": "New Zealand Dollar vs US Dollar",
        "EURJPY": "Euro vs Japanese Yen",
        "EURCHF": "Euro vs Swiss Franc",
        "AUDUSD": "Australian Dollar vs US Dollar",
        "EURNZD": "Euro vs New Zealand Dollar",
        "GBPAUD": "British Pound vs Australian Dollar",
        "GBPCAD": "British Pound vs Canadian Dollar",
        "GBPCHF": "British Pound vs Swiss Franc",
        "GBPNZD": "British Pound vs New Zealand Dollar",
        "AUDCHF": "Australian Dollar vs Swiss Franc",
        "AUDJPY": "Australian Dollar vs Japanese Yen",
        "CADJPY": "Canadian Dollar vs Japanese Yen",
        "CHFJPY": "Swiss Franc vs Japanese Yen",
        "NZDJPY": "New Zealand Dollar vs Japanese Yen",
        "CADCHF": "Canadian Dollar vs Swiss Franc",
        "NZDCAD": "New Zealand Dollar vs Canadian Dollar",
        "NZDCHF": "New Zealand Dollar vs Swiss Franc",
        "EURSEEK": "Euro vs Swedish Krona",
        "EURNOK": "Euro vs Norwegian Krone",
        "USDSEK": "US Dollar vs Swedish Krona",
        "USDNOK": "US Dollar vs Norwegian Krone",
        "USDMXN": "US Dollar vs Mexican Peso",
        "USDZAR": "US Dollar vs South African Rand",
        "USDTRY": "US Dollar vs Turkish Lira",
        "USDSGD": "US Dollar vs Singapore Dollar",
        "USDHKD": "US Dollar vs Hong Kong Dollar",
        "USDCNH": "US Dollar vs Chinese Yuan",
        # Indices
        "CHINA50": "China A50 Index",
        "US30": "Dow Jones Industrial Average",
        "US500": "S&P 500 Index",
        "US100": "Nasdaq 100 Index",
        "UK100": "FTSE 100 Index",
        "GER40": "DAX 40 Index",
        "FRA40": "CAC 40 Index",
        "JPN225": "Nikkei 225 Index",
        "AUS200": "ASX 200 Index",
        "HK50": "Hang Seng Index",
        # Stocks
        "TSLA.NAS": "Tesla Inc",
        "AAPL.NAS": "Apple Inc",
        "GOOGL.NAS": "Alphabet Inc",
        "MSFT.NAS": "Microsoft Corporation",
        "AMZN.NAS": "Amazon.com Inc",
        "META.NAS": "Meta Platforms Inc",
        "NVDA.NAS": "NVIDIA Corporation",
        # Commodities
        "XAUUSD": "Gold vs US Dollar",
        "XAGUSD": "Silver vs US Dollar",
        "USOIL": "WTI Crude Oil",
        "UKOIL": "Brent Crude Oil",
        # Crypto
        "BTCUSD": "Bitcoin vs US Dollar",
        "ETHUSD": "Ethereum vs US Dollar",
    }
    clean_symbol = symbol.replace("/", "").replace("-", "")
    return symbol_names.get(clean_symbol, symbol)


async def get_current_price(symbol: str) -> dict:
    """Get current price data for a symbol (simulated for now)"""
    try:
        clean_symbol = symbol.replace("/", "").replace("-", "")
        
        # Base prices for common symbols
        base_prices = {
            "AUDCAD": 0.95523,
            "EURUSD": 1.08245,
            "GBPUSD": 1.26750,
            "USDJPY": 149.85,
            "GBPJPY": 189.45,
            "EURAUD": 1.6707,
            "AUDNZD": 1.19505,
            "EURGBP": 0.85420,
            "USDCAD": 1.35890,
            "USDCHF": 0.88450,
            "NZDUSD": 0.61250,
            "EURJPY": 162.15,
            "AUDUSD": 0.67850,
            "XAUUSD": 2345.50,
            "XAGUSD": 27.85,
            "USOIL": 78.45,
            "BTCUSD": 67500.00,
            "ETHUSD": 3450.00,
            "CHINA50": 14495,
            "US30": 38950,
            "US500": 5125,
            "US100": 17850,
            "EURSEEK": 10.8830,
            "TSLANAS": 381.61,
        }
        
        base_price = base_prices.get(clean_symbol, 1.0000)
        
        # Add random variation (-0.5% to +0.5%)
        variation = (random.random() - 0.5) * 0.01
        current_price = base_price * (1 + variation)
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        # Format based on symbol type
        if "JPY" in symbol:
            price_str = f"{current_price:.2f}"
            change_str = f"{change:+.2f}"
        elif clean_symbol in ["CHINA50", "US30", "US500", "US100", "UK100", "GER40", "JPN225"]:
            price_str = f"{current_price:.0f}"
            change_str = f"{change:+.0f}"
        elif clean_symbol in ["XAUUSD", "BTCUSD", "ETHUSD"]:
            price_str = f"{current_price:.2f}"
            change_str = f"{change:+.2f}"
        else:
            price_str = f"{current_price:.5f}"
            change_str = f"{change:+.5f}"
        
        change_percent_str = f"{change_percent:+.2f}%"
        
        return {
            "price": price_str,
            "change": change_str,
            "change_percent": change_percent_str
        }
        
    except Exception as e:
        print(f"[SIGNALS] Error getting price for {symbol}: {e}", flush=True)
        return {
            "price": "—",
            "change": "",
            "change_percent": ""
        }


async def get_ohlc_data(symbol: str, timeframe: str) -> list:
    """Get OHLC chart data for pattern visualization (simulated)"""
    try:
        ohlc_data = []
        base_time = datetime.utcnow() - timedelta(hours=48)
        
        # Starting price based on symbol
        clean_symbol = symbol.replace("/", "").replace("-", "")
        base_prices = {
            "AUDCAD": 0.95400, "EURUSD": 1.08200, "GBPUSD": 1.26700,
            "USDJPY": 149.50, "GBPJPY": 189.00, "XAUUSD": 2340.00,
        }
        start_price = base_prices.get(clean_symbol, 1.0000)
        
        for i in range(48):
            timestamp = base_time + timedelta(hours=i)
            
            # Generate realistic OHLC with trend
            trend = 0.0001 if i % 10 < 5 else -0.0001
            open_price = start_price + (random.random() - 0.5) * 0.002 + (i * trend)
            high_price = open_price + random.random() * 0.001
            low_price = open_price - random.random() * 0.001
            close_price = low_price + (high_price - low_price) * random.random()
            
            ohlc_data.append({
                "timestamp": timestamp.isoformat(),
                "open": round(open_price, 5),
                "high": round(high_price, 5),
                "low": round(low_price, 5),
                "close": round(close_price, 5),
                "volume": random.randint(1000, 10000)
            })
            
            start_price = close_price
        
        return ohlc_data
        
    except Exception as e:
        print(f"[SIGNALS] Error getting OHLC data for {symbol}: {e}", flush=True)
        return []


def calculate_expiry_display(expires_at: Optional[datetime]) -> Optional[str]:
    """Calculate human-readable expiry time"""
    if not expires_at:
        return None
    
    now = datetime.utcnow()
    if expires_at <= now:
        return "Expired"
    
    time_diff = expires_at - now
    total_seconds = time_diff.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    
    if hours > 24:
        days = hours // 24
        remaining_hours = hours % 24
        return f"{days}d {remaining_hours}h"
    else:
        return f"{hours}h {minutes}m"


def row_to_signal_response(row: dict, current_price_data: dict = None) -> SignalResponse:
    """Convert database row to SignalResponse"""
    if current_price_data is None:
        current_price_data = {}
    
    return SignalResponse(
        id=row["id"],
        symbol=row.get("symbol", ""),
        full_name=row.get("full_name") or get_full_name_from_symbol(row.get("symbol", "")),
        direction=row.get("direction", "BUY"),
        pattern=row.get("pattern"),
        timeframe=row.get("timeframe", "1H"),
        entry=str(row.get("entry", row.get("entry_price", "0"))),
        target=str(row.get("target", row.get("take_profit", "0"))),
        stop=str(row.get("stop", row.get("stop_loss", "0"))),
        current_price=current_price_data.get("price"),
        price_change=current_price_data.get("change"),
        price_change_percent=current_price_data.get("change_percent"),
        sentiment_bearish=row.get("sentiment_bearish", 50) or 50,
        sentiment_bullish=row.get("sentiment_bullish", 50) or 50,
        confidence=row.get("confidence", row.get("ai_confidence", 75)) or 75,
        expiry=calculate_expiry_display(row.get("expires_at")),
        expires_at=row.get("expires_at"),
        asset_type=row.get("asset_type", "forex") or "forex",
        country=row.get("country", "all") or "all",
        chart_data=None,  # chart_data is JSON, handle separately if needed
        created_at=row.get("created_at", datetime.utcnow()),
        status=row.get("status", "active"),
        ai_confidence=row.get("ai_confidence")
    )


# ══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/active", response_model=List[SignalResponse])
async def get_active_signals(
    confidence: Optional[int] = Query(60, description="Minimum confidence level"),
    asset_type: Optional[str] = Query("all", description="Asset type filter"),
    pattern: Optional[str] = Query("all", description="Pattern type filter"),
    country: Optional[str] = Query("all", description="Country filter"),
    status: Optional[str] = Query("active", description="Status filter"),
    current_user: dict = Depends(get_current_user)
):
    """Get filtered signals with pattern analysis"""
    
    user_tier = current_user.get("subscription_tier", "free")
    
    # Build query
    query = signals.select().where(signals.c.status == "active")
    
    # Apply filters
    if confidence and confidence > 0:
        query = query.where(signals.c.confidence >= confidence)
    
    if asset_type and asset_type != "all":
        query = query.where(signals.c.asset_type == asset_type)
    
    if pattern and pattern != "all":
        query = query.where(signals.c.pattern == pattern.upper())
    
    if country and country != "all":
        from sqlalchemy import or_
        query = query.where(or_(signals.c.country == country, signals.c.country == "all"))
    
    # Order by newest first
    query = query.order_by(signals.c.created_at.desc())
    
    # Limit for free users
    if user_tier == "free":
        query = query.limit(3)
    
    rows = await database.fetch_all(query)
    
    # Enhance with real-time price data
    enhanced_signals = []
    for row in rows:
        row_dict = dict(row)
        try:
            current_price_data = await get_current_price(row_dict.get("symbol", ""))
            enhanced_signals.append(row_to_signal_response(row_dict, current_price_data))
        except Exception as e:
            print(f"[SIGNALS] Error enhancing signal {row_dict.get('id')}: {e}", flush=True)
            enhanced_signals.append(row_to_signal_response(row_dict))
    
    return enhanced_signals


@router.get("/enhanced", response_model=List[SignalResponse])
async def get_enhanced_signals(
    confidence: Optional[int] = Query(60, description="Minimum confidence level"),
    asset_type: Optional[str] = Query("all", description="Asset type filter"),
    pattern: Optional[str] = Query("all", description="Pattern type filter"),
    country: Optional[str] = Query("all", description="Country filter"),
    status: Optional[str] = Query("all", description="Status filter"),
    current_user: dict = Depends(get_current_user)
):
    """Enhanced signals endpoint with all filtering options"""
    return await get_active_signals(
        confidence=confidence,
        asset_type=asset_type,
        pattern=pattern,
        country=country,
        status=status,
        current_user=current_user
    )


@router.get("/all")
async def get_all_signals(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all signals (admin or for history view)"""
    
    query = signals.select()
    
    if status:
        query = query.where(signals.c.status == status)
    
    query = query.order_by(signals.c.created_at.desc()).limit(limit).offset(offset)
    
    rows = await database.fetch_all(query)
    
    # Get total count
    from sqlalchemy import func, select as sa_select
    count_query = sa_select(func.count()).select_from(signals)
    if status:
        count_query = count_query.where(signals.c.status == status)
    total = await database.fetch_val(count_query)
    
    return {
        "signals": [row_to_signal_response(dict(row)) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific signal by ID"""
    
    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    row_dict = dict(row)
    current_price_data = await get_current_price(row_dict.get("symbol", ""))
    
    return row_to_signal_response(row_dict, current_price_data)


@router.get("/{signal_id}/chart-analysis", response_model=ChartAnalysisResponse)
async def get_signal_chart_analysis(
    signal_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed chart analysis for a specific signal"""
    
    user_tier = current_user.get("subscription_tier", "free")
    
    # Free users get limited access
    if user_tier == "free":
        raise HTTPException(
            status_code=402,
            detail="Upgrade to Pro for detailed chart analysis"
        )
    
    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    row_dict = dict(row)
    symbol = row_dict.get("symbol", "")
    timeframe = row_dict.get("timeframe", "1H")
    
    # Get current price and OHLC data
    current_price_data = await get_current_price(symbol)
    ohlc_data = await get_ohlc_data(symbol, timeframe)
    
    signal_response = row_to_signal_response(row_dict, current_price_data)
    
    # Generate analysis
    entry = str(row_dict.get("entry", row_dict.get("entry_price", "0")))
    target = str(row_dict.get("target", row_dict.get("take_profit", "0")))
    stop = str(row_dict.get("stop", row_dict.get("stop_loss", "0")))
    pattern = row_dict.get("pattern", "FLAG")
    direction = row_dict.get("direction", "BUY")
    
    analysis = {
        "pattern_type": pattern,
        "pattern_description": f"{pattern} pattern identified on {timeframe} timeframe",
        "trend_direction": direction,
        "key_levels": {
            "resistance": target if direction == "BUY" else entry,
            "support": stop if direction == "BUY" else target,
            "pivot": entry
        },
        "risk_reward_ratio": calculate_rr_ratio(entry, target, stop),
        "confluence_factors": [
            f"Pattern: {pattern}",
            f"Timeframe: {timeframe}",
            f"Direction: {direction}",
        ],
        "recommendation": f"{'Buy' if direction == 'BUY' else 'Sell'} at {entry}, Target: {target}, Stop: {stop}"
    }
    
    return ChartAnalysisResponse(
        signal=signal_response,
        analysis=analysis,
        chart_levels={
            "entry": entry,
            "target": target,
            "stop": stop,
            "current": current_price_data.get("price", entry)
        },
        ohlc_data=ohlc_data
    )


def calculate_rr_ratio(entry: str, target: str, stop: str) -> str:
    """Calculate risk/reward ratio"""
    try:
        e = float(entry)
        t = float(target)
        s = float(stop)
        
        risk = abs(e - s)
        reward = abs(t - e)
        
        if risk == 0:
            return "N/A"
        
        ratio = reward / risk
        return f"1:{ratio:.1f}"
    except:
        return "N/A"


@router.post("/create", response_model=SignalResponse)
async def create_signal(
    signal_data: SignalCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new signal (admin only)"""
    
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    expires_at = datetime.utcnow() + timedelta(hours=signal_data.expires_in_hours)
    
    insert_query = signals.insert().values(
        symbol=signal_data.symbol,
        full_name=signal_data.full_name,
        direction=signal_data.direction,
        pattern=signal_data.pattern,
        timeframe=signal_data.timeframe,
        entry=signal_data.entry,
        target=signal_data.target,
        stop=signal_data.stop,
        # Also populate legacy columns for backwards compatibility
        entry_price=float(signal_data.entry) if signal_data.entry else 0,
        stop_loss=float(signal_data.stop) if signal_data.stop else 0,
        take_profit=float(signal_data.target) if signal_data.target else 0,
        confidence=signal_data.confidence,
        ai_confidence=signal_data.confidence,
        asset_type=signal_data.asset_type,
        country=signal_data.country,
        sentiment_bearish=signal_data.sentiment_bearish,
        sentiment_bullish=signal_data.sentiment_bullish,
        expires_at=expires_at,
        status="active",
        created_at=datetime.utcnow(),
        is_published=True
    )
    
    signal_id = await database.execute(insert_query)
    
    # Fetch the created signal
    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    
    return row_to_signal_response(dict(row))


@router.put("/{signal_id}")
async def update_signal(
    signal_id: int,
    signal_data: SignalCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing signal (admin only)"""
    
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check signal exists
    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    update_query = signals.update().where(signals.c.id == signal_id).values(
        symbol=signal_data.symbol,
        full_name=signal_data.full_name,
        direction=signal_data.direction,
        pattern=signal_data.pattern,
        timeframe=signal_data.timeframe,
        entry=signal_data.entry,
        target=signal_data.target,
        stop=signal_data.stop,
        entry_price=float(signal_data.entry) if signal_data.entry else 0,
        stop_loss=float(signal_data.stop) if signal_data.stop else 0,
        take_profit=float(signal_data.target) if signal_data.target else 0,
        confidence=signal_data.confidence,
        ai_confidence=signal_data.confidence,
        asset_type=signal_data.asset_type,
        country=signal_data.country,
        sentiment_bearish=signal_data.sentiment_bearish,
        sentiment_bullish=signal_data.sentiment_bullish
    )
    
    await database.execute(update_query)
    
    return {"message": "Signal updated successfully", "id": signal_id}


@router.patch("/{signal_id}/status")
async def update_signal_status(
    signal_id: int,
    status: str = Query(..., description="New status: active, closed, cancelled"),
    result_pips: Optional[float] = Query(None, description="Result in pips if closing"),
    current_user: dict = Depends(get_current_user)
):
    """Update signal status (admin only)"""
    
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    valid_statuses = ["active", "closed", "cancelled", "expired", "hit_tp", "hit_sl"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update_values = {"status": status}
    
    if status in ["closed", "hit_tp", "hit_sl"]:
        update_values["closed_at"] = datetime.utcnow()
        if result_pips is not None:
            update_values["result_pips"] = result_pips
    
    update_query = signals.update().where(signals.c.id == signal_id).values(**update_values)
    await database.execute(update_query)
    
    return {"message": f"Signal status updated to {status}", "id": signal_id}


@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a signal (admin only)"""
    
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check signal exists
    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    delete_query = signals.delete().where(signals.c.id == signal_id)
    await database.execute(delete_query)
    
    return {"message": "Signal deleted successfully", "id": signal_id}


@router.get("/stats/summary")
async def get_signals_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get signals performance summary"""
    
    from sqlalchemy import func, select as sa_select, case
    
    # Total signals
    total_query = sa_select(func.count()).select_from(signals)
    total = await database.fetch_val(total_query)
    
    # Active signals
    active_query = sa_select(func.count()).select_from(signals).where(signals.c.status == "active")
    active = await database.fetch_val(active_query)
    
    # Closed signals (hit TP)
    tp_query = sa_select(func.count()).select_from(signals).where(signals.c.status == "hit_tp")
    hit_tp = await database.fetch_val(tp_query)
    
    # Closed signals (hit SL)
    sl_query = sa_select(func.count()).select_from(signals).where(signals.c.status == "hit_sl")
    hit_sl = await database.fetch_val(sl_query)
    
    # Win rate
    closed_total = (hit_tp or 0) + (hit_sl or 0)
    win_rate = round((hit_tp or 0) / closed_total * 100, 1) if closed_total > 0 else 0
    
    # Total pips
    pips_query = sa_select(func.sum(signals.c.result_pips)).select_from(signals).where(
        signals.c.result_pips.isnot(None)
    )
    total_pips = await database.fetch_val(pips_query) or 0
    
    return {
        "total_signals": total or 0,
        "active_signals": active or 0,
        "closed_signals": closed_total,
        "hit_tp": hit_tp or 0,
        "hit_sl": hit_sl or 0,
        "win_rate": win_rate,
        "total_pips": round(total_pips, 1)
    }
