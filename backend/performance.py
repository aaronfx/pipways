"""
Performance Analytics module - handles trading performance metrics and reporting.
Uses relative imports for package compatibility.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import statistics

from .database import database, trades
from .auth import get_current_user_info

router = APIRouter(prefix="/performance", tags=["performance"])

class TradeStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    total_pnl: float
    average_pnl: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None

class EquityPoint(BaseModel):
    date: str
    pnl: float
    equity: float

class MonthlyStats(BaseModel):
    month: str
    trades: int
    wins: int
    losses: int
    pnl: float
    win_rate: float

def safe_div(numerator: float, denominator: float) -> float:
    """Safe division avoiding ZeroDivisionError."""
    return numerator / denominator if denominator != 0 else 0.0

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(current_user = Depends(get_current_user_info)):
    """Get main dashboard performance stats."""
    try:
        # Query user's trades
        query = trades.select().where(trades.c.user_id == current_user.id)
        user_trades = await database.fetch_all(query)
        
        if not user_trades:
            return {
                "summary": {
                    "total_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "profit_factor": 0
                },
                "recent_trades": [],
                "daily_pnl": []
            }
        
        # Calculate basic stats
        total_trades = len(user_trades)
        pnls = [float(t.pnl) for t in user_trades if hasattr(t, 'pnl')]
        
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p <= 0]
        
        total_profit = sum(winning_trades) if winning_trades else 0
        total_loss = abs(sum(losing_trades)) if losing_trades else 0
        
        stats = {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round((len(winning_trades) / total_trades * 100), 2) if total_trades > 0 else 0,
            "profit_factor": round(total_profit / total_loss, 2) if total_loss > 0 else float('inf'),
            "total_pnl": round(sum(pnls), 2),
            "average_pnl": round(statistics.mean(pnls), 2) if pnls else 0,
            "largest_win": round(max(winning_trades), 2) if winning_trades else 0,
            "largest_loss": round(min(losing_trades), 2) if losing_trades else 0
        }
        
        # Recent trades (last 5)
        recent = sorted(user_trades, key=lambda x: x.entry_time if hasattr(x, 'entry_time') else datetime.min, reverse=True)[:5]
        recent_formatted = []
        for t in recent:
            trade = {
                "id": t.id,
                "symbol": getattr(t, 'symbol', 'Unknown'),
                "pnl": float(getattr(t, 'pnl', 0)),
                "entry_time": str(t.entry_time) if hasattr(t, 'entry_time') else None,
                "side": getattr(t, 'side', 'long')
            }
            recent_formatted.append(trade)
        
        return {
            "summary": stats,
            "recent_trades": recent_formatted,
            "daily_pnl": []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/equity-curve", response_model=List[EquityPoint])
async def get_equity_curve(
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(get_current_user_info)
):
    """Get equity curve for charting."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = trades.select().where(
            (trades.c.user_id == current_user.id) & 
            (trades.c.entry_time >= cutoff_date)
        ).order_by(trades.c.entry_time)
        
        user_trades = await database.fetch_all(query)
        
        equity_curve = []
        running_total = 0
        
        for trade in user_trades:
            pnl = float(getattr(trade, 'pnl', 0))
            running_total += pnl
            
            point = {
                "date": str(getattr(trade, 'entry_time', datetime.utcnow())),
                "pnl": round(pnl, 2),
                "equity": round(running_total, 2)
            }
            equity_curve.append(point)
        
        return equity_curve
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monthly-analysis", response_model=List[MonthlyStats])
async def get_monthly_analysis(current_user = Depends(get_current_user_info)):
    """Get monthly performance breakdown."""
    try:
        query = trades.select().where(trades.c.user_id == current_user.id)
        user_trades = await database.fetch_all(query)
        
        months = {}
        
        for trade in user_trades:
            if not hasattr(trade, 'entry_time') or not trade.entry_time:
                continue
                
            # Extract YYYY-MM
            date_str = str(trade.entry_time)[:7]
            
            if date_str not in months:
                months[date_str] = {
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "pnl": 0.0
                }
            
            months[date_str]["trades"] += 1
            pnl = float(getattr(trade, 'pnl', 0))
            months[date_str]["pnl"] += pnl
            
            if pnl > 0:
                months[date_str]["wins"] += 1
            else:
                months[date_str]["losses"] += 1
        
        # Convert to list and calculate win rates
        result = []
        for month, data in sorted(months.items()):
            stats = {
                "month": month,
                "trades": data["trades"],
                "wins": data["wins"],
                "losses": data["losses"],
                "pnl": round(data["pnl"], 2),
                "win_rate": round((data["wins"] / data["trades"] * 100), 2) if data["trades"] > 0 else 0
            }
            result.append(stats)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trade-distribution")
async def get_trade_distribution(current_user = Depends(get_current_user_info)):
    """Get distribution of trade outcomes."""
    try:
        query = trades.select().where(trades.c.user_id == current_user.id)
        user_trades = await database.fetch_all(query)
        
        distribution = {
            "breakeven": 0,
            "small_win": 0,
            "medium_win": 0,
            "large_win": 0,
            "small_loss": 0,
            "medium_loss": 0,
            "large_loss": 0
        }
        
        for trade in user_trades:
            pnl = float(getattr(trade, 'pnl', 0))
            
            if -1 <= pnl <= 1:
                distribution["breakeven"] += 1
            elif 1 < pnl <= 50:
                distribution["small_win"] += 1
            elif 50 < pnl <= 200:
                distribution["medium_win"] += 1
            elif pnl > 200:
                distribution["large_win"] += 1
            elif -50 <= pnl < -1:
                distribution["small_loss"] += 1
            elif -200 <= pnl < -50:
                distribution["medium_loss"] += 1
            elif pnl < -200:
                distribution["large_loss"] += 1
        
        return {
            "distribution": distribution,
            "total": len(user_trades)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consecutive-analysis")
async def get_consecutive_analysis(current_user = Depends(get_current_user_info)):
    """Analyze winning and losing streaks."""
    try:
        query = trades.select().where(trades.c.user_id == current_user.id).order_by(trades.c.entry_time)
        user_trades = await database.fetch_all(query)
        
        if not user_trades:
            return {
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0,
                "current_streak": 0,
                "current_streak_type": "none"
            }
        
        # Calculate streaks
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for trade in user_trades:
            pnl = float(getattr(trade, 'pnl', 0))
            
            if pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        # Determine current streak
        last_trade = user_trades[-1]
        last_pnl = float(getattr(last_trade, 'pnl', 0))
        
        return {
            "max_consecutive_wins": max_win_streak,
            "max_consecutive_losses": max_loss_streak,
            "current_streak": current_win_streak if last_pnl > 0 else current_loss_streak,
            "current_streak_type": "win" if last_pnl > 0 else "loss"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
