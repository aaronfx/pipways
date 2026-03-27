# Enhanced signals.py for Pipways
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

router = APIRouter()

# Enhanced signal model to include pattern data
class SignalResponse(BaseModel):
    id: int
    symbol: str
    full_name: str
    direction: str  # "BUY STOP" or "SELL STOP"
    pattern: str    # "FLAG", "WEDGE", "PENNANT", "TRIANGLE"
    timeframe: str
    entry: str
    target: str
    stop: str
    current_price: str
    price_change: str
    price_change_percent: str
    sentiment: dict  # {"bearish": 48, "bullish": 52}
    confidence: int
    expiry: str
    asset_type: str  # "forex", "indices", "commodities", "crypto"
    country: str     # "us", "eu", "asia", "all"
    chart_data: Optional[dict] = None  # OHLC and pattern data
    created_at: datetime
    expires_at: datetime
    status: str = "active"

@router.get("/signals/enhanced", response_model=List[SignalResponse])
async def get_enhanced_signals(
    confidence: Optional[int] = 60,
    asset_type: Optional[str] = "all",
    pattern: Optional[str] = "all",
    country: Optional[str] = "all",
    status: Optional[str] = "all",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Get filtered signals with pattern analysis"""
    
    # Apply subscription limits
    user_tier = current_user.get("subscription_tier", "free")
    if user_tier == "free":
        # Free users see limited signals
        limit = await get_feature_limit(db, "signals_visible", "free")
    else:
        limit = None
    
    # Build query with filters
    query = select(Signal).where(Signal.status == "active")
    
    if confidence > 0:
        query = query.where(Signal.confidence >= confidence)
    if asset_type != "all":
        query = query.where(Signal.asset_type == asset_type)
    if pattern != "all":
        query = query.where(Signal.pattern == pattern.upper())
    if country != "all":
        query = query.where(Signal.country == country)
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query.order_by(Signal.created_at.desc()))
    signals = result.scalars().all()
    
    # Add real-time price data and chart info
    enhanced_signals = []
    for signal in signals:
        # Get current price (you'd integrate with a real price feed)
        current_price = await get_current_price(signal.symbol)
        
        enhanced_signal = {
            **signal.__dict__,
            "current_price": current_price["price"],
            "price_change": current_price["change"],
            "price_change_percent": current_price["change_percent"],
            "chart_data": await get_chart_data(signal.symbol, signal.timeframe)
        }
        enhanced_signals.append(enhanced_signal)
    
    return enhanced_signals

@router.get("/signals/{signal_id}/chart-analysis")
async def get_signal_chart_analysis(
    signal_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Get detailed chart analysis for a specific signal"""
    
    signal = await db.get(Signal, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Generate detailed analysis using AI
    analysis = await generate_pattern_analysis(
        symbol=signal.symbol,
        pattern=signal.pattern,
        timeframe=signal.timeframe,
        entry=signal.entry,
        target=signal.target,
        stop=signal.stop
    )
    
    return {
        "signal": signal,
        "analysis": analysis,
        "chart_levels": {
            "entry": signal.entry,
            "target": signal.target,
            "stop": signal.stop,
            "current": await get_current_price(signal.symbol)
        }
    }

async def get_chart_data(symbol: str, timeframe: str):
    """Get OHLC chart data for pattern visualization"""
    # In production, integrate with your price data provider
    # For now, return sample data structure
    return {
        "ohlc": [
            {"o": 0.95426, "h": 0.95547, "l": 0.95352, "c": 0.95523, "timestamp": "2026-03-27T06:00:00Z"},
            # ... more OHLC data
        ],
        "pattern_points": [
            {"type": "flag_top", "price": 0.95600, "timestamp": "2026-03-27T04:00:00Z"},
            {"type": "flag_bottom", "price": 0.95400, "timestamp": "2026-03-27T05:00:00Z"}
        ]
    }
