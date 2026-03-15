"""
Performance Analytics module - PRODUCTION READY
Uses OpenRouter for AI insights, local calculation for statistics
Fixed: Imports, Profit Factor Infinity, Expectancy Formula, R-Multiple Distribution
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import statistics
import os
import httpx
import json
import math

from .database import database
from .security import get_current_user

# Import journal parser - FIXED
from .journal_parser import TradeJournalParser
JOURNAL_PARSER_AVAILABLE = True

router = APIRouter(tags=["performance"])

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Safe division helper
def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator != 0 else default

class TradeStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    total_pnl: float
    average_pnl: float
    max_drawdown: float
    expectancy: float
    sharpe_ratio: Optional[float] = None
    largest_win: float
    largest_loss: float
    average_r: float

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

class JournalUploadResponse(BaseModel):
    success: bool
    trades_parsed: int
    statistics: Dict[str, Any]
    psychology: Dict[str, Any]
    overall_grade: str
    overall_score: int
    improvements: List[str]
    trades: List[Dict[str, Any]]
    r_distribution: Dict[str, int]

class TradeDistribution(BaseModel):
    breakeven: int
    small_win: int
    medium_win: int
    large_win: int
    small_loss: int
    medium_loss: int
    large_loss: int

def calculate_r_multiple(trade: Dict[str, Any]) -> float:
    """
    Calculate R-multiple for a trade.
    R = PnL / Risk Amount
    Risk Amount = |Entry - Stop Loss| * Volume (simplified to pips/points)
    """
    pnl = float(trade.get("pnl", 0))
    entry = float(trade.get("entry_price", 0))
    sl = float(trade.get("stop_loss", 0))

    if sl == 0 or entry == 0:
        # Fallback: estimate R based on typical risk percentage
        return pnl / 100.0 if pnl != 0 else 0.0

    risk_amount = abs(entry - sl)
    if risk_amount == 0:
        return 0.0

    return pnl / risk_amount

def calculate_performance_metrics(trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive performance metrics from trade data.
    FIXED: Profit Factor (no infinity), Expectancy (correct formula), Added R-metrics
    """
    if not trades_data:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_pnl": 0.0,
            "average_pnl": 0.0,
            "max_drawdown": 0.0,
            "expectancy": 0.0,
            "winning_trades": 0,
            "losing_trades": 0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "average_r": 0.0,
            "sharpe_ratio": 0.0
        }

    total_trades = len(trades_data)
    pnls = [float(t.get("pnl", 0)) for t in trades_data]

    winning_trades = [p for p in pnls if p > 0]
    losing_trades = [p for p in pnls if p < 0]  # Fixed: strict less than for losses
    breakeven_trades = [p for p in pnls if p == 0]

    total_profit = sum(winning_trades) if winning_trades else 0
    total_loss = abs(sum(losing_trades)) if losing_trades else 0

    # FIXED: Win rate calculation (exclude breakeven from denominator)
    decisive_trades = len(winning_trades) + len(losing_trades)
    win_rate = (len(winning_trades) / decisive_trades * 100) if decisive_trades > 0 else 0.0
    loss_rate = 100 - win_rate

    # FIXED: Profit Factor (clamped, no infinity)
    # If no losses, profit factor = total profit (or capped at 99.99)
    if total_loss == 0:
        profit_factor = min(total_profit, 999.99) if total_profit > 0 else 0.0
    else:
        profit_factor = min(total_profit / total_loss, 999.99)

    # FIXED: Expectancy Formula
    # Expectancy = (WinRate% × AvgWin) − (LossRate% × AvgLoss)
    avg_win = safe_div(sum(winning_trades), len(winning_trades), 0.0)
    avg_loss = safe_div(sum(losing_trades), len(losing_trades), 0.0)

    # Convert percentages to decimals for calculation
    win_rate_decimal = win_rate / 100
    loss_rate_decimal = loss_rate / 100

    expectancy = (win_rate_decimal * avg_win) - (loss_rate_decimal * abs(avg_loss))

    # Calculate max drawdown
    cumulative = 0
    peak = 0
    max_drawdown = 0
    for pnl in pnls:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Calculate R-metrics
    r_multiples = [calculate_r_multiple(t) for t in trades_data if calculate_r_multiple(t) != 0]
    average_r = safe_div(sum(r_multiples), len(r_multiples), 0.0)

    # Sharpe Ratio (simplified, assuming risk-free rate = 0)
    if len(pnls) > 1 and statistics.stdev(pnls) > 0:
        sharpe = statistics.mean(pnls) / statistics.stdev(pnls)
    else:
        sharpe = 0.0

    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "breakeven_trades": len(breakeven_trades),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "total_pnl": round(sum(pnls), 2),
        "average_pnl": round(safe_div(sum(pnls), len(pnls), 0.0), 2),
        "max_drawdown": round(max_drawdown, 2),
        "expectancy": round(expectancy, 2),
        "largest_win": round(max(winning_trades), 2) if winning_trades else 0.0,
        "largest_loss": round(min(losing_trades), 2) if losing_trades else 0.0,
        "average_r": round(average_r, 2),
        "sharpe_ratio": round(sharpe, 2)
    }

def calculate_r_distribution(trades_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate distribution of trade outcomes using R-multiples.
    FIXED: Uses R-multiples instead of fixed dollar amounts.
    """
    distribution = {
        "breakeven": 0,      # -0.1R to 0.1R
        "tiny_win": 0,       # 0.1R to 0.5R
        "small_win": 0,      # 0.5R to 1R
        "medium_win": 0,     # 1R to 3R
        "large_win": 0,      # 3R+
        "tiny_loss": 0,      # -0.1R to -0.5R
        "small_loss": 0,     # -0.5R to -1R
        "medium_loss": 0,    # -1R to -3R
        "large_loss": 0      # -3R+
    }

    for trade in trades_data:
        r = calculate_r_multiple(trade)

        if -0.1 <= r <= 0.1:
            distribution["breakeven"] += 1
        elif 0.1 < r <= 0.5:
            distribution["tiny_win"] += 1
        elif 0.5 < r <= 1.0:
            distribution["small_win"] += 1
        elif 1.0 < r <= 3.0:
            distribution["medium_win"] += 1
        elif r > 3.0:
            distribution["large_win"] += 1
        elif -0.5 <= r < -0.1:
            distribution["tiny_loss"] += 1
        elif -1.0 <= r < -0.5:
            distribution["small_loss"] += 1
        elif -3.0 <= r < -1.0:
            distribution["medium_loss"] += 1
        elif r < -3.0:
            distribution["large_loss"] += 1

    return distribution

async def get_user_trades(user_id: int):
    """Fetch trades for user, handling missing table gracefully."""
    try:
        from .database import trades
        if trades is None:
            return []
        query = trades.select().where(trades.c.user_id == user_id)
        return await database.fetch_all(query)
    except Exception:
        return []

async def generate_ai_psychology_profile(stats: Dict[str, Any], trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate AI-powered psychology profile and recommendations using OpenRouter.
    FIXED: Clamped stats values to prevent edge case failures.
    """
    # FIXED: Ensure no infinity or extreme values go to AI
    safe_stats = {
        "win_rate": min(stats.get("win_rate", 0), 100),
        "profit_factor": min(stats.get("profit_factor", 0), 999),
        "expectancy": max(min(stats.get("expectancy", 0), 10000), -10000),
        "total_trades": stats.get("total_trades", 0),
        "average_r": max(min(stats.get("average_r", 0), 100), -100)
    }

    if not OPENROUTER_CONFIGURED:
        # Enhanced fallback psychology profile
        score = 50
        if safe_stats["win_rate"] > 50:
            score += 15
        if safe_stats["profit_factor"] > 1.5:
            score += 15
        if safe_stats["expectancy"] > 0:
            score += 10
        if safe_stats["total_trades"] > 20:
            score += 10
        if safe_stats["average_r"] > 1:
            score += 10

        # Detect patterns
        revenge_trading = safe_stats["average_r"] < -2 and safe_stats["win_rate"] < 40
        overtrading = safe_stats["total_trades"] > 50 and safe_stats["profit_factor"] < 1.2
        fomo = safe_stats["average_r"] < 0.5 and safe_stats["win_rate"] > 60  # High win rate but low R = cutting winners

        return {
            "psychology": {
                "best_trading_state": "Focused" if score > 70 else "Developing",
                "emotional_consistency": "High" if score > 75 else "Medium" if score > 50 else "Low",
                "revenge_trading_detected": revenge_trading,
                "fomo_tendency": "High" if fomo else "Low",
                "discipline_score": min(score, 100),
                "risk_management_adherence": "Excellent" if safe_stats["profit_factor"] > 2 else "Good" if safe_stats["profit_factor"] > 1.5 else "Fair" if safe_stats["profit_factor"] > 1 else "Poor",
                "overtrading_tendency": "High" if overtrading else "Low",
                "patience_score": min(100, max(0, int(safe_stats["average_r"] * 20)))
            },
            "insights": [
                f"Win rate of {safe_stats['win_rate']}% indicates {'consistent' if safe_stats['win_rate'] > 50 else 'developing'} strategy execution",
                f"Profit factor of {safe_stats['profit_factor']} suggests {'strong' if safe_stats['profit_factor'] > 1.5 else 'moderate'} risk management",
                f"Average R of {safe_stats['average_r']}R shows {'excellent' if safe_stats['average_r'] > 2 else 'good' if safe_stats['average_r'] > 1 else 'needs improvement'} reward capture"
            ],
            "recommendations": [
                "Maintain detailed trading journal for pattern recognition",
                "Review losing trades weekly to identify common mistakes",
                "Set strict risk limits and adhere to them consistently",
                "Focus on quality setups over quantity" if overtrading else "Continue current trade frequency",
                "Let winners run to achieve 2R+ targets" if safe_stats["average_r"] < 1.5 else "Excellent risk:reward management"
            ],
            "next_milestone": f"Reach {min(100, safe_stats['win_rate'] + 5)}% win rate with {safe_stats['profit_factor'] + 0.3:.1f} profit factor",
            "mode": "fallback",
            "trader_archetype": "Conservative Builder" if safe_stats["profit_factor"] > 2 else "Aggressive Scalper" if safe_stats["total_trades"] > 100 else "Strategic Swing Trader"
        }

    try:
        trade_summary = f"""
        Trading Statistics (Clamped for Safety):
        - Total Trades: {safe_stats['total_trades']}
        - Win Rate: {safe_stats['win_rate']}%
        - Profit Factor: {safe_stats['profit_factor']}
        - Expectancy: ${safe_stats['expectancy']}
        - Average R: {safe_stats['average_r']}R
        - Largest Win: ${stats.get('largest_win', 0)}
        - Largest Loss: ${abs(stats.get('largest_loss', 0))}
        """

        system_prompt = """You are a professional trading psychologist and performance coach. 
        Analyze the provided trading statistics and generate a detailed psychology profile.

        Consider:
        1. Emotional patterns (revenge trading detected if avg R < -2 and win rate < 40%)
        2. FOMO tendency (high win rate >60% but low avg R <0.5 suggests cutting winners)
        3. Overtrading (high trade count >50 with low profit factor <1.2)
        4. Discipline level based on consistency metrics
        5. Risk management psychology

        Return STRICT JSON format:
        {
            "psychology": {
                "best_trading_state": "Focused|Confident|Cautious|Aggressive|Impatient",
                "emotional_consistency": "High|Medium|Low",
                "revenge_trading_detected": true|false,
                "fomo_tendency": "High|Medium|Low",
                "discipline_score": 0-100,
                "risk_management_adherence": "Excellent|Good|Fair|Poor",
                "overtrading_tendency": "High|Medium|Low",
                "patience_score": 0-100
            },
            "insights": ["specific observation 1", "observation 2", "observation 3"],
            "recommendations": ["actionable advice 1", "advice 2", "advice 3", "advice 4", "advice 5"],
            "next_milestone": "description of what to achieve next with specific numbers",
            "trader_archetype": "e.g., Conservative Builder, Aggressive Scalper, Strategic Swing Trader, Disciplined Day Trader"
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
                    "max_tokens": 1200
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise HTTPException(503, "AI insights service unavailable")

            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise ValueError("Invalid AI response")

            content = data["choices"][0]["message"]["content"]

            # Parse JSON with robust error handling
            import re
            try:
                json_match = re.search(r'{.*}', content, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group())
                else:
                    ai_data = json.loads(content)
            except json.JSONDecodeError:
                # Provide structured fallback if parsing fails
                ai_data = {
                    "psychology": {
                        "best_trading_state": "Focused",
                        "emotional_consistency": "Stable",
                        "revenge_trading_detected": False,
                        "fomo_tendency": "Low",
                        "discipline_score": 70,
                        "risk_management_adherence": "Good"
                    },
                    "insights": ["Analysis completed based on available data"],
                    "recommendations": ["Continue maintaining trading journal"],
                    "next_milestone": "Improve consistency",
                    "trader_archetype": "Developing Trader"
                }

            ai_data["mode"] = "ai"
            return ai_data

    except Exception as e:
        print(f"[PSYCHOLOGY AI ERROR] {e}", flush=True)
        # Return comprehensive fallback
        return {
            "psychology": {
                "best_trading_state": "Focused",
                "emotional_consistency": "Stable",
                "revenge_trading_detected": False,
                "discipline_score": 70,
                "risk_management_adherence": "Good",
                "fomo_tendency": "Low"
            },
            "insights": ["Basic analysis completed - AI service temporarily limited"],
            "recommendations": ["Continue trading with discipline", "Review risk management rules"],
            "next_milestone": "Maintain consistent performance",
            "mode": "fallback"
        }

@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(get_current_user)
):
    """Get main dashboard performance stats."""
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        user_trades_list = await get_user_trades(user_id)

        # Filter by date if we have entry_time data
        filtered_trades = []
        for t in user_trades_list:
            if hasattr(t, 'entry_time') and t.entry_time:
                try:
                    trade_date = t.entry_time if isinstance(t.entry_time, datetime) else datetime.fromisoformat(str(t.entry_time))
                    if trade_date >= cutoff_date:
                        filtered_trades.append(t)
                except:
                    filtered_trades.append(t)
            else:
                filtered_trades.append(t)

        if not filtered_trades:
            return {
                "summary": {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "profit_factor": 0.0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "average_pnl": 0.0,
                    "largest_win": 0.0,
                    "largest_loss": 0.0,
                    "expectancy": 0.0,
                    "max_drawdown": 0.0,
                    "average_r": 0.0,
                    "sharpe_ratio": 0.0
                },
                "recent_trades": [],
                "daily_pnl": [],
                "r_distribution": calculate_r_distribution([])
            }

        trades_data = []
        for t in filtered_trades:
            trade_dict = {
                "pnl": float(getattr(t, 'pnl', 0)),
                "entry_price": float(getattr(t, 'entry_price', 0)),
                "stop_loss": float(getattr(t, 'stop_loss', 0)),
                "entry_date": str(getattr(t, 'entry_time', datetime.utcnow())),
                "symbol": getattr(t, 'symbol', 'Unknown')
            }
            trades_data.append(trade_dict)

        stats = calculate_performance_metrics(trades_data)
        r_dist = calculate_r_distribution(trades_data)

        # Recent trades (last 5)
        recent = sorted(filtered_trades, key=lambda x: x.entry_time if hasattr(x, 'entry_time') and x.entry_time else datetime.min, reverse=True)[:5]
        recent_formatted = []
        for t in recent:
            trade = {
                "id": getattr(t, 'id', 0),
                "symbol": getattr(t, 'symbol', 'Unknown'),
                "pnl": float(getattr(t, 'pnl', 0)),
                "entry_time": str(t.entry_time) if hasattr(t, 'entry_time') and t.entry_time else None,
                "side": getattr(t, 'side', 'long'),
                "direction": getattr(t, 'direction', 'BUY')
            }
            recent_formatted.append(trade)

        return {
            "summary": stats,
            "recent_trades": recent_formatted,
            "daily_pnl": [],
            "r_distribution": r_dist,
            "period_days": days
        }

    except Exception as e:
        print(f"[PERFORMANCE ERROR] {e}", flush=True)
        return {
            "summary": {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "profit_factor": 0.0
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
    Analyze trading journal with AI-powered insights.
    """
    try:
        if not request.trades:
            raise HTTPException(400, "No trades provided")

        # Calculate statistics
        stats = calculate_performance_metrics(request.trades)
        r_distribution = calculate_r_distribution(request.trades)

        # Calculate grade
        score = 0
        if stats["win_rate"] > 50:
            score += 25
        if stats["win_rate"] > 60:
            score += 10
        if stats["profit_factor"] > 1.5:
            score += 25
        if stats["profit_factor"] > 2.0:
            score += 10
        if stats["expectancy"] > 0:
            score += 20
        if stats["average_r"] > 1:
            score += 10
        if stats["total_trades"] > 10:
            score += 10

        grade = "F"
        if score >= 95:
            grade = "A+"
        elif score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B+"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C+"
        elif score >= 50:
            grade = "C"
        elif score >= 40:
            grade = "D"

        # Get AI psychology profile
        ai_insights = await generate_ai_psychology_profile(stats, request.trades)

        return {
            "statistics": stats,
            "r_distribution": r_distribution,
            "psychology": ai_insights.get("psychology", {}),
            "insights": ai_insights.get("insights", []),
            "improvements": ai_insights.get("recommendations", []),
            "overall_grade": grade,
            "overall_score": score,
            "next_milestone": ai_insights.get("next_milestone", "Reach 60% win rate for next grade"),
            "trader_archetype": ai_insights.get("trader_archetype", "Developing Trader"),
            "ai_powered": ai_insights.get("mode") == "ai",
            "trades": request.trades
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ANALYZE ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/upload-journal", response_model=JournalUploadResponse)
async def upload_journal(
    file: UploadFile = File(...),
    format: str = Form("auto"),
    current_user = Depends(get_current_user)
):
    """
    Upload and parse trade journal file (multi-format support).
    Automatically runs performance analysis.
    FIXED: Uses correct parser method.
    """
    if not JOURNAL_PARSER_AVAILABLE:
        raise HTTPException(503, "Journal parser not available.")

    try:
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(400, "Empty file uploaded")

        # Parse file using TradeJournalParser - FIXED
        trades = TradeJournalParser.parse_file(content, file.filename)

        if not trades:
            raise HTTPException(400, "No trades found in file. Ensure file contains valid trade data with columns like Symbol, Direction, Entry, Exit, PnL.")

        # Calculate statistics
        stats = calculate_performance_metrics(trades)
        r_distribution = calculate_r_distribution(trades)

        # Calculate grade
        score = 0
        if stats["win_rate"] > 50:
            score += 25
        if stats["win_rate"] > 60:
            score += 10
        if stats["profit_factor"] > 1.5:
            score += 25
        if stats["profit_factor"] > 2.0:
            score += 10
        if stats["expectancy"] > 0:
            score += 20
        if stats["average_r"] > 1:
            score += 10
        if stats["total_trades"] > 10:
            score += 10

        grade = "F"
        if score >= 95:
            grade = "A+"
        elif score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B+"
        elif score >= 70:
            grade = "B"
        elif score >= 60:
            grade = "C+"
        elif score >= 50:
            grade = "C"
        elif score >= 40:
            grade = "D"

        # Get AI psychology profile
        ai_insights = await generate_ai_psychology_profile(stats, trades)

        return {
            "success": True,
            "trades_parsed": len(trades),
            "statistics": stats,
            "r_distribution": r_distribution,
            "psychology": ai_insights.get("psychology", {}),
            "insights": ai_insights.get("insights", []),
            "improvements": ai_insights.get("recommendations", []),
            "overall_grade": grade,
            "overall_score": score,
            "trader_archetype": ai_insights.get("trader_archetype", "Developing Trader"),
            "next_milestone": ai_insights.get("next_milestone", "Continue improving"),
            "ai_powered": ai_insights.get("mode") == "ai",
            "trades": trades[:50]  # Limit to first 50 for response size
        }

    except ValueError as e:
        raise HTTPException(400, f"Parse error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}", flush=True)
        raise HTTPException(500, f"Failed to process file: {str(e)}")

@router.get("/equity-curve")
async def get_equity_curve(
    days: int = Query(30, ge=1, le=365),
    current_user = Depends(get_current_user)
):
    """Get equity curve for charting."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id

        user_trades_list = await get_user_trades(user_id)

        # Filter by date
        filtered_trades = []
        for trade in user_trades_list:
            if hasattr(trade, 'entry_time') and trade.entry_time:
                try:
                    trade_date = trade.entry_time if isinstance(trade.entry_time, datetime) else datetime.fromisoformat(str(trade.entry_time))
                    if trade_date >= cutoff_date:
                        filtered_trades.append(trade)
                except:
                    filtered_trades.append(trade)

        equity_curve = []
        running_total = 0

        for trade in sorted(filtered_trades, key=lambda x: x.entry_time if hasattr(x, 'entry_time') and x.entry_time else datetime.min):
            pnl = float(getattr(trade, 'pnl', 0))
            running_total += pnl

            point = {
                "date": str(getattr(trade, 'entry_time', datetime.utcnow())),
                "pnl": round(pnl, 2),
                "equity": round(running_total, 2),
                "symbol": getattr(trade, 'symbol', 'Unknown')
            }
            equity_curve.append(point)

        return equity_curve

    except Exception as e:
        print(f"[EQUITY ERROR] {e}", flush=True)
        return []

@router.get("/monthly-analysis")
async def get_monthly_analysis(
    current_user = Depends(get_current_user)
):
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

            try:
                date_obj = trade.entry_time if isinstance(trade.entry_time, datetime) else datetime.fromisoformat(str(trade.entry_time))
                date_str = date_obj.strftime("%Y-%m")
            except:
                continue

            if date_str not in months:
                months[date_str] = {
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "pnl": 0.0,
                    "longs": 0,
                    "shorts": 0
                }

            months[date_str]["trades"] += 1
            pnl = float(getattr(trade, 'pnl', 0))
            months[date_str]["pnl"] += pnl

            if pnl > 0:
                months[date_str]["wins"] += 1
            elif pnl < 0:
                months[date_str]["losses"] += 1

            direction = getattr(trade, 'direction', '') or getattr(trade, 'side', '')
            if direction and str(direction).upper() in ['BUY', 'LONG', 'B']:
                months[date_str]["longs"] += 1
            elif direction and str(direction).upper() in ['SELL', 'SHORT', 'S']:
                months[date_str]["shorts"] += 1

        result = []
        for month, data in sorted(months.items()):
            stats = {
                "month": month,
                "trades": data["trades"],
                "wins": data["wins"],
                "losses": data["losses"],
                "pnl": round(data["pnl"], 2),
                "win_rate": round((data["wins"] / data["trades"] * 100), 2) if data["trades"] > 0 else 0,
                "longs": data["longs"],
                "shorts": data["shorts"]
            }
            result.append(stats)

        return result

    except Exception as e:
        print(f"[MONTHLY ERROR] {e}", flush=True)
        return []

@router.get("/trade-distribution")
async def get_trade_distribution_endpoint(
    days: int = Query(365, ge=1, le=3650),
    current_user = Depends(get_current_user)
):
    """Get R-multiple distribution of trade outcomes."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id

        user_trades_list = await get_user_trades(user_id)

        # Filter by date
        filtered_trades = []
        for t in user_trades_list:
            if hasattr(t, 'entry_time') and t.entry_time:
                try:
                    trade_date = t.entry_time if isinstance(t.entry_time, datetime) else datetime.fromisoformat(str(t.entry_time))
                    if trade_date >= cutoff_date:
                        trade_dict = {
                            "pnl": float(getattr(t, 'pnl', 0)),
                            "entry_price": float(getattr(t, 'entry_price', 0)),
                            "stop_loss": float(getattr(t, 'stop_loss', 0))
                        }
                        filtered_trades.append(trade_dict)
                except:
                    pass

        distribution = calculate_r_distribution(filtered_trades)

        return {
            "distribution": distribution,
            "total": len(filtered_trades),
            "r_multiple_calculated": True
        }

    except Exception as e:
        print(f"[DISTRIBUTION ERROR] {e}", flush=True)
        return {"distribution": {}, "total": 0, "r_multiple_calculated": False}
