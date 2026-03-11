"""
Performance Analytics Routes
Endpoints: /api/performance/*
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from .database import db_pool
from .security import get_current_user, get_admin_user
from .schemas import PerformanceAnalysisRequest
import json

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.post("/analyze")
async def analyze_performance(
    request: PerformanceAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze trading performance"""
    # Calculate metrics
    trades = request.trades or []
    total_trades = len(trades)

    if total_trades == 0:
        return {"error": "No trades provided"}

    wins = sum(1 for t in trades if t.get("result") == "WIN")
    losses = sum(1 for t in trades if t.get("result") == "LOSS")
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    # Calculate profit/loss
    total_pips = sum(t.get("pips", 0) for t in trades)
    avg_pips_per_trade = total_pips / total_trades if total_trades > 0 else 0

    # Risk metrics
    profits = [t.get("pips", 0) for t in trades if t.get("pips", 0) > 0]
    losses_pips = [abs(t.get("pips", 0)) for t in trades if t.get("pips", 0) < 0]

    avg_win = sum(profits) / len(profits) if profits else 0
    avg_loss = sum(losses_pips) / len(losses_pips) if losses_pips else 0

    profit_factor = sum(profits) / sum(losses_pips) if losses_pips and sum(losses_pips) > 0 else float('inf')

    # Calculate trader score (0-100)
    score_components = {
        "win_rate": min(win_rate, 100) * 0.3,
        "profit_factor": min(profit_factor, 5) * 10 if profit_factor != float('inf') else 50,
        "consistency": 20 if total_trades >= 20 else (total_trades / 20) * 20,
        "risk_management": 20 if avg_loss < avg_win * 0.5 else 10
    }
    trader_score = sum(score_components.values())

    analysis_data = {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "total_pips": round(total_pips, 2),
        "avg_pips_per_trade": round(avg_pips_per_trade, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else None,
        "avg_win_pips": round(avg_win, 2),
        "avg_loss_pips": round(avg_loss, 2),
        "trader_score": round(trader_score, 0),
        "account_balance": request.account_balance,
        "trading_period_days": request.trading_period_days
    }

    # Save to database
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO performance_analyses (user_id, analysis_data, raw_trades, trader_score)
            VALUES ($1, $2, $3, $4)
        """, current_user["id"], json.dumps(analysis_data), json.dumps(trades), int(trader_score))

    return analysis_data

@router.get("/history")
async def get_performance_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get performance analysis history"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, analysis_data, trader_score, created_at
            FROM performance_analyses
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, current_user["id"], limit)

        return [dict(row) for row in rows]
