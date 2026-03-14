"""
Performance Analytics module - FIXED
Uses OpenRouter for AI insights, local calculation for statistics
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import statistics
import os
import httpx

from .database import database
try:
    from .database import trades
except ImportError:
    trades = None

from .security import get_current_user

router = APIRouter(tags=["performance"])

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

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

class JournalRequest(BaseModel):
    trades: List[Dict[str, Any]]

def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator != 0 else 0.0

def calculate_performance_metrics(trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive performance metrics from trade data.
    Pure local calculation - no AI required.
    """
    if not trades_data:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_pnl": 0,
            "average_pnl": 0,
            "max_drawdown": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "expectancy": 0
        }
    
    total_trades = len(trades_data)
    pnls = [float(t.get("pnl", 0)) for t in trades_data]
    
    winning_trades = [p for p in pnls if p > 0]
    losing_trades = [p for p in pnls if p <= 0]
    
    total_profit = sum(winning_trades) if winning_trades else 0
    total_loss = abs(sum(losing_trades)) if losing_trades else 0
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    
    # Calculate expectancy
    avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0
    loss_rate = 100 - win_rate
    expectancy = ((avg_win * win_rate) + (avg_loss * loss_rate)) / 100 if total_trades > 0 else 0
    
    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(total_profit / total_loss, 2) if total_loss > 0 else float('inf'),
        "total_pnl": round(sum(pnls), 2),
        "average_pnl": round(statistics.mean(pnls), 2) if pnls else 0,
        "max_drawdown": round(min(pnls), 2) if pnls else 0,
        "expectancy": round(expectancy, 2),
        "largest_win": round(max(winning_trades), 2) if winning_trades else 0,
        "largest_loss": round(min(losing_trades), 2) if losing_trades else 0
    }

async def get_user_trades(user_id: int):
    """Fetch trades for user, handling missing table gracefully."""
    if trades is None:
        return []
    
    try:
        query = trades.select().where(trades.c.user_id == user_id)
        return await database.fetch_all(query)
    except Exception:
        return []

async def generate_ai_insights(stats: Dict[str, Any], trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate AI-powered psychology profile and recommendations using OpenRouter.
    Returns 503 if OpenRouter not configured.
    """
    if not OPENROUTER_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail="AI insights not configured. Set OPENROUTER_API_KEY."
        )
    
    try:
        # Prepare trade summary for AI
        trade_summary = f"""
        Trading Statistics:
        - Total Trades: {stats['total_trades']}
        - Win Rate: {stats['win_rate']}%
        - Profit Factor: {stats['profit_factor']}
        - Total P&L: ${stats['total_pnl']}
        - Average Trade: ${stats['average_pnl']}
        - Expectancy: ${stats['expectancy']}
        - Largest Win: ${stats['largest_win']}
        - Largest Loss: ${stats['largest_loss']}
        """
        
        system_prompt = """You are a professional trading psychologist and performance coach. 
        Analyze the provided trading statistics and generate:
        1. A trading psychology profile (best state, consistency level, emotional patterns)
        2. Specific behavioral insights based on the metrics
        3. 3-4 personalized improvement recommendations
        
        Return STRICT JSON format:
        {
            "psychology": {
                "best_trading_state": "Focused|Confident|Cautious|Aggressive etc",
                "emotional_consistency": "High|Medium|Low",
                "revenge_trading_detected": true|false,
                "fomo_tendency": "High|Medium|Low",
                "discipline_score": 0-100
            },
            "insights": ["specific observation 1", "observation 2", "observation 3"],
            "recommendations": ["actionable advice 1", "advice 2", "advice 3", "advice 4"],
            "next_milestone": "description of what to achieve next"
        }"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://pipwaysapp.onrender.com",
                    "X-Title": "Pipways Trading Platform",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze these trading results and provide psychology profile:\n{trade_summary}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"[PERFORMANCE AI ERROR] HTTP {response.status_code}: {response.text}", flush=True)
                raise HTTPException(503, "AI insights service unavailable")
            
            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise HTTPException(503, "Invalid AI response")
            
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON response
            import json
            import re
            
            try:
                # Extract JSON
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group())
                else:
                    ai_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback if AI returns non-JSON
                ai_data = {
                    "psychology": {
                        "best_trading_state": "Focused",
                        "emotional_consistency": "Stable",
                        "revenge_trading_detected": False,
                        "fomo_tendency": "Low",
                        "discipline_score": 75
                    },
                    "insights": ["Analysis completed", "Review your risk management"],
                    "recommendations": ["Keep a detailed trading journal", "Stick to your trading plan"],
                    "next_milestone": "Maintain consistent risk per trade"
                }
            
            return ai_data
            
    except httpx.TimeoutException:
        raise HTTPException(504, "AI insights request timed out")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PERFORMANCE AI ERROR] {e}", flush=True)
        raise HTTPException(503, "AI insights service error")

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(current_user = Depends(get_current_user)):
    """Get main dashboard performance stats."""
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        
        user_trades_list = await get_user_trades(user_id)
        
        if not user_trades_list:
            return {
                "summary": {
                    "total_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "profit_factor": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "average_pnl": 0,
                    "largest_win": 0,
                    "largest_loss": 0,
                    "expectancy": 0
                },
                "recent_trades": [],
                "daily_pnl": []
            }
        
        # Calculate stats
        total_trades = len(user_trades_list)
        pnls = [float(t.pnl) for t in user_trades_list if hasattr(t, 'pnl')]
        
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
        recent = sorted(user_trades_list, key=lambda x: x.entry_time if hasattr(x, 'entry_time') else datetime.min, reverse=True)[:5]
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
        print(f"[PERFORMANCE ERROR] {e}", flush=True)
        return {
            "summary": {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "profit_factor": 0
            },
            "recent_trades": [],
            "daily_pnl": [],
            "error": str(e)
        }

@router.post("/analyze-journal")
async def analyze_journal(
    request: JournalRequest, 
    current_user = Depends(get_current_user)
):
    """
    Analyze trading journal with AI-powered insights using OpenRouter.
    Returns 503 if OpenRouter not configured.
    """
    try:
        if not request.trades:
            raise HTTPException(400, "No trades provided")
        
        # Step 1: Calculate local statistics (always accurate)
        stats = calculate_performance_metrics(request.trades)
        
        # Step 2: Calculate grade
        score = 0
        if stats["win_rate"] > 50:
            score += 30
        if stats["profit_factor"] > 1.5:
            score += 30
        if stats["total_pnl"] > 0:
            score += 20
        if stats["total_trades"] > 10:
            score += 20
        
        grade = "F"
        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B+"
        elif score >= 60:
            grade = "B"
        elif score >= 50:
            grade = "C"
        
        # Step 3: Get AI insights from OpenRouter
        try:
            ai_insights = await generate_ai_insights(stats, request.trades)
            
            return {
                "statistics": stats,
                "psychology": ai_insights.get("psychology", {
                    "best_trading_state": "Focused",
                    "emotional_consistency": "Stable",
                    "revenge_trading_detected": False
                }),
                "insights": ai_insights.get("insights", []),
                "improvements": ai_insights.get("recommendations", ["Keep maintaining your discipline"]),
                "overall_grade": grade,
                "overall_score": score,
                "next_milestone": ai_insights.get("next_milestone", "Reach 60% win rate for next grade"),
                "ai_powered": True
            }
            
        except HTTPException as he:
            # If AI unavailable, return basic analysis without AI features
            if he.status_code == 503:
                # Generate basic recommendations based on stats
                basic_improvements = []
                if stats["win_rate"] < 50:
                    basic_improvements.append("Improve win rate by cutting losses faster")
                if stats["profit_factor"] < 1.5:
                    basic_improvements.append("Work on risk/reward ratio - aim for 1:2 minimum")
                if stats["total_pnl"] < 0:
                    basic_improvements.append("Consider paper trading to refine strategy")
                if not basic_improvements:
                    basic_improvements.append("Keep maintaining your discipline")
                
                return {
                    "statistics": stats,
                    "psychology": {
                        "best_trading_state": "Focused",
                        "emotional_consistency": "Stable",
                        "revenge_trading_detected": False,
                        "discipline_score": min(score, 100)
                    },
                    "insights": ["Basic analysis completed - AI insights unavailable"],
                    "improvements": basic_improvements,
                    "overall_grade": grade,
                    "overall_score": score,
                    "next_milestone": "Reach 60% win rate for next grade",
                    "ai_powered": False,
                    "warning": "AI insights service not configured. Set OPENROUTER_API_KEY for personalized analysis."
                }
            raise he
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ANALYZE ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/equity-curve", response_model=List[EquityPoint])
async def get_equity_curve(
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(get_current_user)
):
    """Get equity curve for charting."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        
        if trades is None:
            return []
            
        query = trades.select().where(
            (trades.c.user_id == user_id) & 
            (trades.c.entry_time >= cutoff_date)
        ).order_by(trades.c.entry_time)
        
        user_trades_list = await database.fetch_all(query)
        
        equity_curve = []
        running_total = 0
        
        for trade in user_trades_list:
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
        print(f"[EQUITY ERROR] {e}", flush=True)
        return []

@router.get("/monthly-analysis", response_model=List[MonthlyStats])
async def get_monthly_analysis(current_user = Depends(get_current_user)):
    """Get monthly performance breakdown."""
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        user_trades_list = await get_user_trades(user_id)
        
        if not user_trades_list:
            return []
        
        months = {}
        
        for trade in user_trades_list:
            if not hasattr(trade, 'entry_time') or not trade.entry_time:
                continue
                
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
        print(f"[MONTHLY ERROR] {e}", flush=True)
        return []

@router.get("/trade-distribution")
async def get_trade_distribution(current_user = Depends(get_current_user)):
    """Get distribution of trade outcomes."""
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        user_trades_list = await get_user_trades(user_id)
        
        distribution = {
            "breakeven": 0,
            "small_win": 0,
            "medium_win": 0,
            "large_win": 0,
            "small_loss": 0,
            "medium_loss": 0,
            "large_loss": 0
        }
        
        for trade in user_trades_list:
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
            "total": len(user_trades_list)
        }
        
    except Exception as e:
        print(f"[DISTRIBUTION ERROR] {e}", flush=True)
        return {"distribution": {}, "total": 0}
