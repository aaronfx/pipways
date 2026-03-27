from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc, func
from typing import List, Optional
import json
from datetime import datetime, timedelta
import asyncio
import httpx
from pydantic import BaseModel

from .database import get_database
from .models import Signal, User
from .auth import get_current_user
from .subscriptions import check_feature_access, get_feature_limit
from .ai_services import generate_pattern_analysis

router = APIRouter()

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

@router.get("/active", response_model=List[SignalResponse])
async def get_active_signals(
    confidence: Optional[int] = Query(60, description="Minimum confidence level"),
    asset_type: Optional[str] = Query("all", description="Asset type filter"),
    pattern: Optional[str] = Query("all", description="Pattern type filter"),
    country: Optional[str] = Query("all", description="Country filter"),
    status: Optional[str] = Query("active", description="Status filter"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Get filtered signals with pattern analysis"""
    
    # Check feature access and limits
    user_tier = current_user.get("subscription_tier", "free")
    
    if user_tier == "free":
        limit = await get_feature_limit(db, "signals_visible", "free")
        if limit is None:
            limit = 3  # Default for free users
    else:
        limit = None
    
    # Build query
    query = select(Signal).where(Signal.status == "active")
    
    # Apply filters
    if confidence > 0:
        query = query.where(Signal.confidence >= confidence)
    
    if asset_type != "all":
        query = query.where(Signal.asset_type == asset_type)
    
    if pattern != "all":
        query = query.where(Signal.pattern == pattern.upper())
    
    if country != "all":
        query = query.where(or_(Signal.country == country, Signal.country == "all"))
    
    # Apply limit for free users
    if limit:
        query = query.limit(limit)
    
    query = query.order_by(desc(Signal.created_at))
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    # Enhance signals with real-time data
    enhanced_signals = []
    for signal in signals:
        try:
            # Get current price and calculate changes
            current_price_data = await get_current_price(signal.symbol)
            
            # Calculate time remaining
            expiry_time = None
            if signal.expires_at:
                now = datetime.utcnow()
                if signal.expires_at > now:
                    time_diff = signal.expires_at - now
                    hours = int(time_diff.total_seconds() // 3600)
                    minutes = int((time_diff.total_seconds() % 3600) // 60)
                    
                    if hours > 24:
                        days = hours // 24
                        remaining_hours = hours % 24
                        expiry_time = f"{days}d {remaining_hours}h"
                    else:
                        expiry_time = f"{hours}h {minutes}m"
                else:
                    expiry_time = "Expired"
            
            enhanced_signal = SignalResponse(
                id=signal.id,
                symbol=signal.symbol,
                full_name=signal.full_name or get_full_name_from_symbol(signal.symbol),
                direction=signal.direction,
                pattern=signal.pattern,
                timeframe=signal.timeframe,
                entry=signal.entry,
                target=signal.target,
                stop=signal.stop,
                current_price=current_price_data.get("price", signal.entry),
                price_change=current_price_data.get("change", ""),
                price_change_percent=current_price_data.get("change_percent", ""),
                sentiment_bearish=signal.sentiment_bearish or 50,
                sentiment_bullish=signal.sentiment_bullish or 50,
                confidence=signal.confidence,
                expiry=expiry_time,
                expires_at=signal.expires_at,
                asset_type=signal.asset_type or "forex",
                country=signal.country or "all",
                chart_data=signal.chart_data,
                created_at=signal.created_at,
                status=signal.status,
                ai_confidence=signal.ai_confidence
            )
            enhanced_signals.append(enhanced_signal)
            
        except Exception as e:
            print(f"Error enhancing signal {signal.id}: {e}")
            # Fallback to basic signal data
            enhanced_signal = SignalResponse(
                id=signal.id,
                symbol=signal.symbol,
                full_name=signal.full_name or get_full_name_from_symbol(signal.symbol),
                direction=signal.direction,
                pattern=signal.pattern,
                timeframe=signal.timeframe,
                entry=signal.entry,
                target=signal.target,
                stop=signal.stop,
                confidence=signal.confidence,
                asset_type=signal.asset_type or "forex",
                country=signal.country or "all",
                created_at=signal.created_at,
                status=signal.status,
                ai_confidence=signal.ai_confidence
            )
            enhanced_signals.append(enhanced_signal)
    
    return enhanced_signals

@router.get("/enhanced", response_model=List[SignalResponse])
async def get_enhanced_signals(
    confidence: Optional[int] = Query(60, description="Minimum confidence level"),
    asset_type: Optional[str] = Query("all", description="Asset type filter"),
    pattern: Optional[str] = Query("all", description="Pattern type filter"),
    country: Optional[str] = Query("all", description="Country filter"),
    status: Optional[str] = Query("all", description="Status filter"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Enhanced signals endpoint with all filtering options"""
    return await get_active_signals(
        confidence=confidence,
        asset_type=asset_type,
        pattern=pattern,
        country=country,
        status=status,
        current_user=current_user,
        db=db
    )

@router.get("/{signal_id}/chart-analysis", response_model=ChartAnalysisResponse)
async def get_signal_chart_analysis(
    signal_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Get detailed chart analysis for a specific signal"""
    
    # Check if user has access to detailed analysis
    user_tier = current_user.get("subscription_tier", "free")
    if user_tier == "free":
        can_access = await check_feature_access(db, current_user["id"], "signals_detailed_analysis", 1)
        if not can_access:
            raise HTTPException(status_code=402, detail="Upgrade to Pro for detailed chart analysis")
    
    # Get signal
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Generate detailed analysis
    try:
        analysis = await generate_pattern_analysis(
            symbol=signal.symbol,
            pattern=signal.pattern or "FLAG",
            timeframe=signal.timeframe,
            entry=signal.entry,
            target=signal.target,
            stop=signal.stop
        )
        
        # Get current price data
        current_price_data = await get_current_price(signal.symbol)
        
        # Get OHLC data for chart
        ohlc_data = await get_ohlc_data(signal.symbol, signal.timeframe)
        
        # Build response
        signal_response = SignalResponse(
            id=signal.id,
            symbol=signal.symbol,
            full_name=signal.full_name or get_full_name_from_symbol(signal.symbol),
            direction=signal.direction,
            pattern=signal.pattern,
            timeframe=signal.timeframe,
            entry=signal.entry,
            target=signal.target,
            stop=signal.stop,
            current_price=current_price_data.get("price", signal.entry),
            price_change=current_price_data.get("change", ""),
            price_change_percent=current_price_data.get("change_percent", ""),
            sentiment_bearish=signal.sentiment_bearish or 50,
            sentiment_bullish=signal.sentiment_bullish or 50,
            confidence=signal.confidence,
            asset_type=signal.asset_type or "forex",
            country=signal.country or "all",
            created_at=signal.created_at,
            status=signal.status,
            ai_confidence=signal.ai_confidence
        )
        
        return ChartAnalysisResponse(
            signal=signal_response,
            analysis=analysis,
            chart_levels={
                "entry": signal.entry,
                "target": signal.target,
                "stop": signal.stop,
                "current": current_price_data.get("price", signal.entry)
            },
            ohlc_data=ohlc_data
        )
        
    except Exception as e:
        print(f"Error generating analysis for signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate chart analysis")

@router.post("/create", response_model=SignalResponse)
async def create_signal(
    signal_data: SignalCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Create a new signal (admin only)"""
    
    # Check if user is admin
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Calculate expiry time
    expires_at = datetime.utcnow() + timedelta(hours=signal_data.expires_in_hours)
    
    # Create signal
    new_signal = Signal(
        symbol=signal_data.symbol,
        full_name=signal_data.full_name,
        direction=signal_data.direction,
        pattern=signal_data.pattern,
        timeframe=signal_data.timeframe,
        entry=signal_data.entry,
        target=signal_data.target,
        stop=signal_data.stop,
        confidence=signal_data.confidence,
        asset_type=signal_data.asset_type,
        country=signal_data.country,
        sentiment_bearish=signal_data.sentiment_bearish,
        sentiment_bullish=signal_data.sentiment_bullish,
        expires_at=expires_at,
        status="active",
        ai_confidence=signal_data.confidence
    )
    
    db.add(new_signal)
    await db.commit()
    await db.refresh(new_signal)
    
    # Send signal alerts to Pro users (if enabled)
    asyncio.create_task(send_signal_alerts(new_signal.id, db))
    
    return SignalResponse(
        id=new_signal.id,
        symbol=new_signal.symbol,
        full_name=new_signal.full_name or get_full_name_from_symbol(new_signal.symbol),
        direction=new_signal.direction,
        pattern=new_signal.pattern,
        timeframe=new_signal.timeframe,
        entry=new_signal.entry,
        target=new_signal.target,
        stop=new_signal.stop,
        confidence=new_signal.confidence,
        asset_type=new_signal.asset_type or "forex",
        country=new_signal.country or "all",
        created_at=new_signal.created_at,
        status=new_signal.status,
        expires_at=new_signal.expires_at,
        ai_confidence=new_signal.ai_confidence
    )

@router.put("/{signal_id}")
async def update_signal(
    signal_id: int,
    signal_data: SignalCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Update an existing signal (admin only)"""
    
    # Check if user is admin
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get signal
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Update signal
    signal.symbol = signal_data.symbol
    signal.full_name = signal_data.full_name
    signal.direction = signal_data.direction
    signal.pattern = signal_data.pattern
    signal.timeframe = signal_data.timeframe
    signal.entry = signal_data.entry
    signal.target = signal_data.target
    signal.stop = signal_data.stop
    signal.confidence = signal_data.confidence
    signal.asset_type = signal_data.asset_type
    signal.country = signal_data.country
    signal.sentiment_bearish = signal_data.sentiment_bearish
    signal.sentiment_bullish = signal_data.sentiment_bullish
    signal.ai_confidence = signal_data.confidence
    
    await db.commit()
    return {"message": "Signal updated successfully"}

@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """Delete a signal (admin only)"""
    
    # Check if user is admin
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get signal
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Delete signal
    await db.delete(signal)
    await db.commit()
    
    return {"message": "Signal deleted successfully"}

# Helper functions

async def get_current_price(symbol: str) -> dict:
    """Get current price data for a symbol"""
    try:
        # In production, integrate with a real price feed (Alpha Vantage, Yahoo Finance, etc.)
        # For now, simulate price data
        
        # Remove any slashes or special characters
        clean_symbol = symbol.replace("/", "").replace("-", "")
        
        # Simulate price movement
        import random
        base_prices = {
            "AUDCAD": 0.95523,
            "EURUSD": 1.08245,
            "GBPJPY": 189.45,
            "CHINA50": 14495,
            "EURAUD": 1.6707,
            "AUDNZD": 1.19505,
            "TSLANAS": 381.61,
            "EURSEEK": 10.8830
        }
        
        base_price = base_prices.get(clean_symbol, 1.0000)
        
        # Add random variation (-0.5% to +0.5%)
        variation = (random.random() - 0.5) * 0.01
        current_price = base_price * (1 + variation)
        change = current_price - base_price
        change_percent = (change / base_price) * 100
        
        # Format based on symbol type
        if "JPY" in symbol or symbol == "CHINA50":
            price_str = f"{current_price:.0f}" if symbol == "CHINA50" else f"{current_price:.2f}"
        else:
            price_str = f"{current_price:.5f}"
        
        change_str = f"{change:+.5f}" if "JPY" not in symbol and symbol != "CHINA50" else f"{change:+.2f}"
        change_percent_str = f"{change_percent:+.2f}%"
        
        return {
            "price": price_str,
            "change": change_str,
            "change_percent": change_percent_str
        }
        
    except Exception as e:
        print(f"Error getting price for {symbol}: {e}")
        return {
            "price": "1.0000",
            "change": "+0.0000",
            "change_percent": "+0.00%"
        }

async def get_ohlc_data(symbol: str, timeframe: str) -> list:
    """Get OHLC chart data for pattern visualization"""
    try:
        # In production, integrate with TradingView, Alpha Vantage, or similar
        # For now, return sample OHLC data structure
        
        import random
        from datetime import datetime, timedelta
        
        ohlc_data = []
        base_time = datetime.utcnow() - timedelta(hours=48)
        
        for i in range(48):  # 48 hours of 1H data
            timestamp = base_time + timedelta(hours=i)
            
            # Generate realistic OHLC data
            open_price = 0.95400 + (random.random() - 0.5) * 0.002
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
        
        return ohlc_data
        
    except Exception as e:
        print(f"Error getting OHLC data for {symbol}: {e}")
        return []

def get_full_name_from_symbol(symbol: str) -> str:
    """Convert symbol to full name"""
    symbol_names = {
        "AUDCAD": "Australian Dollar vs Canadian Dollar",
        "EURUSD": "Euro vs US Dollar",
        "GBPJPY": "British Pound vs Japanese Yen",
        "EURAUD": "Euro vs Australian Dollar",
        "AUDNZD": "Australian Dollar vs New Zealand Dollar",
        "EUR/SEK": "Euro vs Swedish Krona",
        "CHINA50": "China A50 Index",
        "TSLA.NAS": "Tesla Inc",
        "AAPL.NAS": "Apple Inc",
        "GOOGL.NAS": "Alphabet Inc"
    }
    
    return symbol_names.get(symbol.replace("/", ""), symbol)

async def send_signal_alerts(signal_id: int, db: AsyncSession):
    """Send email alerts to Pro users about new signals"""
    try:
        # Get the signal
        result = await db.execute(select(Signal).where(Signal.id == signal_id))
        signal = result.scalar_one_or_none()
        
        if not signal:
            return
        
        # Get Pro users who opted in for signal alerts
        query = select(User).where(
            and_(
                User.subscription_tier.in_(["pro", "enterprise"]),
                User.is_active == True
            )
        )
        
        result = await db.execute(query)
        pro_users = result.scalars().all()
        
        # Send alerts (implement based on your email service)
        from .email_service import send_signal_alert_email
        
        for user in pro_users:
            try:
                await send_signal_alert_email(
                    user.email,
                    user.full_name or user.email,
                    signal
                )
            except Exception as e:
                print(f"Error sending alert to {user.email}: {e}")
                continue
        
        print(f"Signal alerts sent for signal {signal_id}")
        
    except Exception as e:
        print(f"Error sending signal alerts: {e}")
