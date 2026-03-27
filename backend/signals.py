"""
Enhanced Signals API - Rewritten for databases library pattern
Compatible with Pipways FastAPI + databases stack

FIX 1: Changed signals.c.confidence → signals.c.ai_confidence
FIX 2: Added /enhanced endpoint that was missing (causing 422 errors)
       Route order fixed: /enhanced comes BEFORE /{signal_id}

UPDATE: Added AnalysisIQ fields to SignalResponse for Pattern Trade Ideas.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import random

from .database import database, signals, users
from .auth import get_current_user

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════════════════════

class AnalysisIQData(BaseModel):
    pattern_type: str
    order_type: str
    timeframe: str
    status: str
    expiry_timestamp: Optional[str] = None
    technical_summary: Optional[str] = None
    volatility_index: Optional[int] = None
    signal_age_minutes: Optional[int] = None


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
    is_pattern_idea: bool = False
    analysis_iq: Optional[AnalysisIQData] = None

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
    is_pattern_idea: bool = False
    technical_summary: Optional[str] = None
    volatility_index: Optional[int] = None


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_full_name_from_symbol(symbol: str) -> str:
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
        "AUDUSD": "Australian Dollar vs US Dollar",
        "EURSEEK": "Euro vs Swedish Krona",
        "CHINA50": "China A50 Index",
        "US30": "Dow Jones Industrial Average",
        "US500": "S&P 500 Index",
        "US100": "Nasdaq 100 Index",
        "GER40": "DAX 40 Index",
        "XAUUSD": "Gold vs US Dollar",
        "XAGUSD": "Silver vs US Dollar",
        "BTCUSD": "Bitcoin vs US Dollar",
        "ETHUSD": "Ethereum vs US Dollar",
    }
    return symbol_names.get(symbol.replace("/", "").replace("-", ""), symbol)


async def get_current_price(symbol: str) -> dict:
    try:
        clean_symbol = symbol.replace("/", "").replace("-", "")
        base_prices = {
            "AUDCAD": 0.95523, "EURUSD": 1.08245, "GBPUSD": 1.26750,
            "USDJPY": 149.85, "GBPJPY": 189.45, "USDCAD": 1.35890,
            "NZDUSD": 0.61250, "EURJPY": 162.15, "AUDUSD": 0.67850,
            "XAUUSD": 2345.50, "XAGUSD": 27.85, "BTCUSD": 67500.00,
            "ETHUSD": 3450.00, "CHINA50": 14495, "US30": 38950,
            "US100": 17850, "EURSEEK": 10.8830, "EURGBP": 0.85420,
            "USDCHF": 0.88450, "GER40": 18250,
        }
        base_price = base_prices.get(clean_symbol, 1.0000)
        variation = (random.random() - 0.5) * 0.01
        current_price = base_price * (1 + variation)
        change = current_price - base_price
        change_percent = (change / base_price) * 100

        if "JPY" in symbol:
            return {"price": f"{current_price:.2f}", "change": f"{change:+.2f}", "change_percent": f"{change_percent:+.2f}%"}
        elif clean_symbol in ["CHINA50", "US30", "US100", "GER40"]:
            return {"price": f"{current_price:.0f}", "change": f"{change:+.0f}", "change_percent": f"{change_percent:+.2f}%"}
        elif clean_symbol in ["XAUUSD", "BTCUSD", "ETHUSD"]:
            return {"price": f"{current_price:.2f}", "change": f"{change:+.2f}", "change_percent": f"{change_percent:+.2f}%"}
        else:
            return {"price": f"{current_price:.5f}", "change": f"{change:+.5f}", "change_percent": f"{change_percent:+.2f}%"}
    except Exception as e:
        print(f"[SIGNALS] Error getting price for {symbol}: {e}", flush=True)
        return {"price": "—", "change": "", "change_percent": ""}


def calculate_expiry_display(expires_at: Optional[datetime]) -> Optional[str]:
    if not expires_at:
        return None
    now = datetime.utcnow()
    if expires_at <= now:
        return "Expired"
    time_diff = expires_at - now
    hours = int(time_diff.total_seconds() // 3600)
    minutes = int((time_diff.total_seconds() % 3600) // 60)
    if hours > 24:
        return f"{hours // 24}d {hours % 24}h"
    return f"{hours}h {minutes}m"


def build_analysis_iq(row: dict, created_at: datetime, expires_at: Optional[datetime]) -> Optional[AnalysisIQData]:
    pattern = row.get("pattern")
    if not pattern:
        return None

    direction = row.get("direction", "BUY")
    order_type = "BUY STOP" if "BUY" in direction.upper() else "SELL STOP"
    
    status_map = {"active": "LIVE TRADE", "hit_tp": "CLOSED - PROFIT", "hit_sl": "CLOSED - LOSS", "expired": "EXPIRED"}
    iq_status = status_map.get(row.get("status", "active"), "LIVE TRADE")
    
    now = datetime.utcnow()
    age_minutes = int((now - created_at).total_seconds() / 60) if created_at else None
    
    entry = row.get("entry", row.get("entry_price", ""))
    target = row.get("target", row.get("take_profit", ""))
    stop = row.get("stop", row.get("stop_loss", ""))
    timeframe = row.get("timeframe", "4H")
    
    summaries = {
        "FLAG": f"Bull flag on {timeframe}. Entry {entry}, target {target}, stop {stop}.",
        "WEDGE": f"Wedge compression on {timeframe}. Entry {entry}, stop {stop}.",
        "PENNANT": f"Pennant continuation on {timeframe}. Entry {entry}, target {target}.",
        "TRIANGLE": f"Triangle breakout on {timeframe}. Entry {entry}, target {target}.",
        "HEAD_SHOULDERS": f"H&S pattern on {timeframe}. Entry {entry}, target {target}.",
        "DOUBLE_BOTTOM": f"Double bottom reversal on {timeframe}. Entry {entry}, target {target}.",
        "DOUBLE_TOP": f"Double top reversal on {timeframe}. Entry {entry}, target {target}.",
        "BREAKOUT": f"Structural breakout on {timeframe}. Entry {entry}, target {target}.",
        "REVERSAL": f"Reversal signal on {timeframe}. Entry {entry}, target {target}.",
        "SUPPORT": f"Support bounce on {timeframe}. Entry {entry}, target {target}.",
        "RESISTANCE": f"Resistance rejection on {timeframe}. Entry {entry}, target {target}.",
    }
    
    return AnalysisIQData(
        pattern_type=pattern.upper().replace("_", " "),
        order_type=order_type,
        timeframe=timeframe,
        status=iq_status,
        expiry_timestamp=expires_at.isoformat() if expires_at else None,
        technical_summary=row.get("technical_summary") or summaries.get(pattern.upper(), f"{pattern} on {timeframe}."),
        volatility_index=row.get("volatility_index") or random.randint(30, 85),
        signal_age_minutes=age_minutes,
    )


def row_to_signal_response(row: dict, current_price_data: dict = None) -> SignalResponse:
    if current_price_data is None:
        current_price_data = {}

    created_at = row.get("created_at") or datetime.utcnow()
    expires_at = row.get("expires_at")
    is_pattern_idea = bool(row.get("is_pattern_idea", False))
    
    analysis_iq = None
    if is_pattern_idea:
        analysis_iq = build_analysis_iq(row, created_at, expires_at)

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
        expiry=calculate_expiry_display(expires_at),
        expires_at=expires_at,
        asset_type=row.get("asset_type", "forex") or "forex",
        country=row.get("country", "all") or "all",
        chart_data=None,
        created_at=created_at,
        status=row.get("status", "active"),
        ai_confidence=row.get("ai_confidence"),
        is_pattern_idea=is_pattern_idea,
        analysis_iq=analysis_iq,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS - IMPORTANT: Static routes MUST come BEFORE /{signal_id}
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=List[SignalResponse])
async def get_signals(
    asset_type: Optional[str] = None,
    country: Optional[str] = None,
    confidence: Optional[int] = None,
    pattern: Optional[str] = None,
    status: Optional[str] = "active",
    is_pattern_idea: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all signals with optional filters."""
    query = signals.select()
    if status and status != "all":
        query = query.where(signals.c.status == status)
    if asset_type and asset_type != "all":
        query = query.where(signals.c.asset_type == asset_type)
    if country and country != "all":
        query = query.where(signals.c.country == country)
    if confidence is not None:
        query = query.where(signals.c.ai_confidence >= confidence)
    if pattern and pattern != "all":
        query = query.where(signals.c.pattern == pattern.upper())
    if is_pattern_idea is not None:
        query = query.where(signals.c.is_pattern_idea == is_pattern_idea)

    query = query.order_by(signals.c.created_at.desc())
    rows = await database.fetch_all(query)

    result = []
    for row in rows:
        row_dict = dict(row)
        price_data = await get_current_price(row_dict["symbol"])
        result.append(row_to_signal_response(row_dict, price_data))
    return result


@router.get("/enhanced", response_model=List[SignalResponse])
async def get_enhanced_signals(
    confidence: Optional[int] = Query(60, description="Minimum confidence level"),
    asset_type: Optional[str] = Query("all", description="Asset type filter"),
    pattern: Optional[str] = Query("all", description="Pattern type filter"),
    country: Optional[str] = Query("all", description="Country filter"),
    status: Optional[str] = Query("active", description="Status filter"),
    view: Optional[str] = Query("all", description="View: 'all', 'standard', 'analysis_iq'"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get enhanced signals - primary endpoint for frontend.
    This MUST be defined BEFORE /{signal_id} to avoid route conflicts.
    """
    query = signals.select()
    
    if status and status != "all":
        query = query.where(signals.c.status == status)
    if confidence and confidence > 0:
        query = query.where(signals.c.ai_confidence >= confidence)
    if asset_type and asset_type != "all":
        query = query.where(signals.c.asset_type == asset_type)
    if pattern and pattern != "all":
        query = query.where(signals.c.pattern == pattern.upper())
    if country and country != "all":
        from sqlalchemy import or_
        query = query.where(or_(signals.c.country == country, signals.c.country == "all"))
    if view == "analysis_iq":
        query = query.where(signals.c.is_pattern_idea == True)
    elif view == "standard":
        query = query.where(signals.c.is_pattern_idea == False)

    query = query.order_by(signals.c.created_at.desc())
    rows = await database.fetch_all(query)
    
    result = []
    for row in rows:
        row_dict = dict(row)
        try:
            price_data = await get_current_price(row_dict.get("symbol", ""))
            result.append(row_to_signal_response(row_dict, price_data))
        except Exception as e:
            print(f"[SIGNALS] Error processing signal {row_dict.get('id')}: {e}", flush=True)
            result.append(row_to_signal_response(row_dict))
    return result


@router.get("/active", response_model=List[SignalResponse])
async def get_active_signals(current_user: dict = Depends(get_current_user)):
    """Get active signals sorted by confidence."""
    query = signals.select().where(signals.c.status == "active").order_by(signals.c.ai_confidence.desc())
    rows = await database.fetch_all(query)

    result = []
    for row in rows:
        row_dict = dict(row)
        price_data = await get_current_price(row_dict["symbol"])
        result.append(row_to_signal_response(row_dict, price_data))
    return result


@router.get("/stats/summary")
async def get_signals_summary(current_user: dict = Depends(get_current_user)):
    """Get signals performance summary."""
    from sqlalchemy import func, select as sa_select

    total = await database.fetch_val(sa_select(func.count()).select_from(signals))
    active = await database.fetch_val(sa_select(func.count()).select_from(signals).where(signals.c.status == "active"))
    hit_tp = await database.fetch_val(sa_select(func.count()).select_from(signals).where(signals.c.status == "hit_tp"))
    hit_sl = await database.fetch_val(sa_select(func.count()).select_from(signals).where(signals.c.status == "hit_sl"))

    closed_total = (hit_tp or 0) + (hit_sl or 0)
    win_rate = round((hit_tp or 0) / closed_total * 100, 1) if closed_total > 0 else 0

    return {
        "total_signals": total or 0,
        "active_signals": active or 0,
        "closed_signals": closed_total,
        "hit_tp": hit_tp or 0,
        "hit_sl": hit_sl or 0,
        "win_rate": win_rate,
    }


# ══════════════════════════════════════════════════════════════════════════════
# DYNAMIC ID ROUTES - MUST COME AFTER /enhanced, /active, /stats
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: int, current_user: dict = Depends(get_current_user)):
    """Get a single signal by ID."""
    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")

    row_dict = dict(row)
    price_data = await get_current_price(row_dict["symbol"])
    return row_to_signal_response(row_dict, price_data)


@router.post("/", response_model=SignalResponse)
async def create_signal(signal_data: SignalCreateRequest, current_user: dict = Depends(get_current_user)):
    """Create a signal (admin only)."""
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    now = datetime.utcnow()
    values = {
        "symbol": signal_data.symbol.upper(),
        "full_name": signal_data.full_name or get_full_name_from_symbol(signal_data.symbol),
        "direction": signal_data.direction.upper(),
        "pattern": signal_data.pattern.upper() if signal_data.pattern else None,
        "timeframe": signal_data.timeframe,
        "entry": signal_data.entry,
        "entry_price": float(signal_data.entry),
        "target": signal_data.target,
        "take_profit": float(signal_data.target),
        "stop": signal_data.stop,
        "stop_loss": float(signal_data.stop),
        "confidence": signal_data.confidence,
        "ai_confidence": signal_data.confidence,
        "asset_type": signal_data.asset_type,
        "country": signal_data.country,
        "sentiment_bearish": signal_data.sentiment_bearish,
        "sentiment_bullish": signal_data.sentiment_bullish,
        "status": "active",
        "is_published": True,
        "created_at": now,
        "expires_at": now + timedelta(hours=signal_data.expires_in_hours),
        "is_pattern_idea": signal_data.is_pattern_idea,
        "technical_summary": signal_data.technical_summary,
        "volatility_index": signal_data.volatility_index,
    }

    signal_id = await database.execute(signals.insert().values(**values))
    row = dict(await database.fetch_one(signals.select().where(signals.c.id == signal_id)))
    price_data = await get_current_price(row["symbol"])
    return row_to_signal_response(row, price_data)


@router.delete("/{signal_id}")
async def delete_signal(signal_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a signal (admin only)."""
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    query = signals.select().where(signals.c.id == signal_id)
    row = await database.fetch_one(query)
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found")

    await database.execute(signals.delete().where(signals.c.id == signal_id))
    return {"message": "Signal deleted successfully", "id": signal_id}


# ══════════════════════════════════════════════════════════════════════════════
# SEED DATA
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/seed")
async def seed_sample_signals(current_user: dict = Depends(get_current_user)):
    """Seed sample signals (admin only)."""
    if not current_user.get("is_admin", False) and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    count = await database.fetch_val("SELECT COUNT(*) FROM signals WHERE status = 'active'")
    if count and count > 0:
        return {"message": f"Signals already exist ({count} active)", "seeded": 0}

    sample_signals = [
        # AI-DRIVEN (confidence >= 75)
        {'symbol': 'EURUSD', 'full_name': 'Euro vs US Dollar', 'direction': 'BUY', 'pattern': 'BREAKOUT', 'timeframe': '4H', 'entry': '1.08250', 'target': '1.08850', 'stop': '1.07850', 'entry_price': 1.08250, 'take_profit': 1.08850, 'stop_loss': 1.07850, 'confidence': 88, 'ai_confidence': 88, 'asset_type': 'forex', 'country': 'EU', 'sentiment_bearish': 25, 'sentiment_bullish': 75, 'status': 'active', 'is_published': True, 'is_pattern_idea': False},
        {'symbol': 'GBPUSD', 'full_name': 'British Pound vs US Dollar', 'direction': 'BUY', 'pattern': 'FLAG', 'timeframe': '1H', 'entry': '1.26750', 'target': '1.27350', 'stop': '1.26350', 'entry_price': 1.26750, 'take_profit': 1.27350, 'stop_loss': 1.26350, 'confidence': 82, 'ai_confidence': 82, 'asset_type': 'forex', 'country': 'UK', 'sentiment_bearish': 30, 'sentiment_bullish': 70, 'status': 'active', 'is_published': True, 'is_pattern_idea': False},
        {'symbol': 'USDJPY', 'full_name': 'US Dollar vs Japanese Yen', 'direction': 'SELL', 'pattern': 'REVERSAL', 'timeframe': '4H', 'entry': '149.850', 'target': '148.850', 'stop': '150.350', 'entry_price': 149.850, 'take_profit': 148.850, 'stop_loss': 150.350, 'confidence': 79, 'ai_confidence': 79, 'asset_type': 'forex', 'country': 'JP', 'sentiment_bearish': 65, 'sentiment_bullish': 35, 'status': 'active', 'is_published': True, 'is_pattern_idea': False},
        {'symbol': 'AUDUSD', 'full_name': 'Australian Dollar vs US Dollar', 'direction': 'BUY', 'pattern': 'SUPPORT', 'timeframe': '1H', 'entry': '0.67850', 'target': '0.68450', 'stop': '0.67450', 'entry_price': 0.67850, 'take_profit': 0.68450, 'stop_loss': 0.67450, 'confidence': 85, 'ai_confidence': 85, 'asset_type': 'forex', 'country': 'AU', 'sentiment_bearish': 28, 'sentiment_bullish': 72, 'status': 'active', 'is_published': True, 'is_pattern_idea': False},
        {'symbol': 'US30', 'full_name': 'Dow Jones Industrial Average', 'direction': 'BUY', 'pattern': 'BREAKOUT', 'timeframe': '1H', 'entry': '38950', 'target': '39250', 'stop': '38700', 'entry_price': 38950, 'take_profit': 39250, 'stop_loss': 38700, 'confidence': 84, 'ai_confidence': 84, 'asset_type': 'indices', 'country': 'US', 'sentiment_bearish': 22, 'sentiment_bullish': 78, 'status': 'active', 'is_published': True, 'is_pattern_idea': False},
        {'symbol': 'XAUUSD', 'full_name': 'Gold vs US Dollar', 'direction': 'BUY', 'pattern': 'SUPPORT', 'timeframe': '4H', 'entry': '2345.50', 'target': '2385.00', 'stop': '2320.00', 'entry_price': 2345.50, 'take_profit': 2385.00, 'stop_loss': 2320.00, 'confidence': 86, 'ai_confidence': 86, 'asset_type': 'commodities', 'country': 'all', 'sentiment_bearish': 20, 'sentiment_bullish': 80, 'status': 'active', 'is_published': True, 'is_pattern_idea': False},
        {'symbol': 'BTCUSD', 'full_name': 'Bitcoin vs US Dollar', 'direction': 'BUY', 'pattern': 'BREAKOUT', 'timeframe': '4H', 'entry': '67500', 'target': '72000', 'stop': '64500', 'entry_price': 67500, 'take_profit': 72000, 'stop_loss': 64500, 'confidence': 77, 'ai_confidence': 77, 'asset_type': 'crypto', 'country': 'all', 'sentiment_bearish': 32, 'sentiment_bullish': 68, 'status': 'active', 'is_published': True, 'is_pattern_idea': False},

        # PATTERN IDEAS (AnalysisIQ)
        {'symbol': 'AUDCAD', 'full_name': 'Australian Dollar vs Canadian Dollar', 'direction': 'BUY', 'pattern': 'FLAG', 'timeframe': '1H', 'entry': '0.95426', 'target': '0.95800', 'stop': '0.95200', 'entry_price': 0.95426, 'take_profit': 0.95800, 'stop_loss': 0.95200, 'confidence': 72, 'ai_confidence': 72, 'asset_type': 'forex', 'country': 'AU', 'sentiment_bearish': 35, 'sentiment_bullish': 65, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
        {'symbol': 'NZDUSD', 'full_name': 'New Zealand Dollar vs US Dollar', 'direction': 'BUY', 'pattern': 'FLAG', 'timeframe': '4H', 'entry': '0.61250', 'target': '0.61750', 'stop': '0.60900', 'entry_price': 0.61250, 'take_profit': 0.61750, 'stop_loss': 0.60900, 'confidence': 68, 'ai_confidence': 68, 'asset_type': 'forex', 'country': 'NZ', 'sentiment_bearish': 38, 'sentiment_bullish': 62, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
        {'symbol': 'EURSEEK', 'full_name': 'Euro vs Swedish Krona', 'direction': 'SELL', 'pattern': 'WEDGE', 'timeframe': '4H', 'entry': '10.8830', 'target': '10.8400', 'stop': '10.9100', 'entry_price': 10.8830, 'take_profit': 10.8400, 'stop_loss': 10.9100, 'confidence': 70, 'ai_confidence': 70, 'asset_type': 'forex', 'country': 'EU', 'sentiment_bearish': 58, 'sentiment_bullish': 42, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
        {'symbol': 'GBPJPY', 'full_name': 'British Pound vs Japanese Yen', 'direction': 'BUY', 'pattern': 'WEDGE', 'timeframe': '1H', 'entry': '189.450', 'target': '190.450', 'stop': '188.750', 'entry_price': 189.450, 'take_profit': 190.450, 'stop_loss': 188.750, 'confidence': 74, 'ai_confidence': 74, 'asset_type': 'forex', 'country': 'UK', 'sentiment_bearish': 32, 'sentiment_bullish': 68, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
        {'symbol': 'CHINA50', 'full_name': 'China A50 Index', 'direction': 'BUY', 'pattern': 'PENNANT', 'timeframe': '1H', 'entry': '14495', 'target': '14650', 'stop': '14380', 'entry_price': 14495, 'take_profit': 14650, 'stop_loss': 14380, 'confidence': 78, 'ai_confidence': 78, 'asset_type': 'indices', 'country': 'CN', 'sentiment_bearish': 28, 'sentiment_bullish': 72, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
        {'symbol': 'XAGUSD', 'full_name': 'Silver vs US Dollar', 'direction': 'BUY', 'pattern': 'TRIANGLE', 'timeframe': '4H', 'entry': '27.850', 'target': '28.550', 'stop': '27.350', 'entry_price': 27.850, 'take_profit': 28.550, 'stop_loss': 27.350, 'confidence': 71, 'ai_confidence': 71, 'asset_type': 'commodities', 'country': 'all', 'sentiment_bearish': 40, 'sentiment_bullish': 60, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
        {'symbol': 'ETHUSD', 'full_name': 'Ethereum vs US Dollar', 'direction': 'BUY', 'pattern': 'DOUBLE_BOTTOM', 'timeframe': '4H', 'entry': '3450', 'target': '3650', 'stop': '3300', 'entry_price': 3450, 'take_profit': 3650, 'stop_loss': 3300, 'confidence': 69, 'ai_confidence': 69, 'asset_type': 'crypto', 'country': 'all', 'sentiment_bearish': 42, 'sentiment_bullish': 58, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
        {'symbol': 'GER40', 'full_name': 'DAX 40 Index', 'direction': 'SELL', 'pattern': 'DOUBLE_TOP', 'timeframe': '1H', 'entry': '18250', 'target': '17950', 'stop': '18450', 'entry_price': 18250, 'take_profit': 17950, 'stop_loss': 18450, 'confidence': 66, 'ai_confidence': 66, 'asset_type': 'indices', 'country': 'DE', 'sentiment_bearish': 58, 'sentiment_bullish': 42, 'status': 'active', 'is_published': True, 'is_pattern_idea': True},
    ]

    seeded = 0
    expiry_hours = [24, 36, 48, 72]

    for i, signal in enumerate(sample_signals):
        try:
            signal['created_at'] = datetime.utcnow()
            signal['expires_at'] = datetime.utcnow() + timedelta(hours=expiry_hours[i % len(expiry_hours)])
            await database.execute(signals.insert().values(**signal))
            seeded += 1
            tag = "AnalysisIQ" if signal.get("is_pattern_idea") else "AI-Driven"
            print(f"[SIGNALS] ✅ Seeded [{tag}]: {signal['symbol']} ({signal['pattern']})", flush=True)
        except Exception as e:
            print(f"[SIGNALS] ❌ Failed to seed {signal['symbol']}: {e}", flush=True)

    return {"message": f"Seeded {seeded} signals", "seeded": seeded}
