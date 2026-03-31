"""
Performance Analytics Module - UPGRADED VERSION
Advanced trading analytics with AI coaching, equity curves, and risk analysis
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import statistics
import os
import httpx
import json
import re
from collections import defaultdict

from .database import database
from .auth import get_current_user
from .subscriptions import check_limit, log_usage
from .journal_parser import TradeJournalParser

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
    breakeven_trades: int
    win_rate: float
    loss_rate: float
    profit_factor: float
    total_pnl: float
    net_pnl: float
    average_pnl: float
    average_win: float
    average_loss: float
    max_drawdown: float
    expectancy: float
    winning_streak: int
    losing_streak: int
    risk_consistency_score: float
    detected_strategy: str

class EquityPoint(BaseModel):
    date: str
    trade_number: int
    pnl: float
    equity: float

class MonthlyPerformance(BaseModel):
    month: str
    year: int
    trades: int
    wins: int
    losses: int
    breakeven: int
    pnl: float
    win_rate: float

class TradeDistribution(BaseModel):
    wins: int
    losses: int
    breakeven: int

class AICoachAnalysis(BaseModel):
    discipline_score: int
    risk_management_score: int
    strategy_consistency: int
    main_mistake: str
    recommendation: str
    detected_patterns: List[str]
    strengths: List[str]
    improvements: List[str]

class PerformanceResponse(BaseModel):
    total_trades: int
    win_rate: float
    profit_factor: float
    net_pnl: float
    expectancy: float
    max_drawdown: float
    winning_streak: int
    losing_streak: int
    equity_curve: List[Dict[str, Any]]
    trade_distribution: Dict[str, int]
    monthly_performance: List[Dict[str, Any]]
    ai_coach: Optional[Dict[str, Any]]
    risk_consistency_score: float
    detected_strategy: str
    overall_grade: str
    overall_score: int

# Safe division helper
def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator != 0 else default

def calculate_equity_curve(trades: List[Dict]) -> List[Dict]:
    """Calculate equity curve - running balance after each trade"""
    equity_curve = []
    balance = 0

    for i, trade in enumerate(trades):
        pnl = float(trade.get("pnl", 0))
        balance += pnl

        equity_curve.append({
            "trade_number": i + 1,
            "date": trade.get("entry_date", ""),
            "pnl": round(pnl, 2),
            "equity": round(balance, 2)
        })

    return equity_curve

def calculate_max_drawdown(trades: List[Dict]) -> float:
    """Calculate maximum drawdown from equity peak"""
    if not trades:
        return 0.0

    balance = 0
    peak = 0
    max_drawdown = 0

    for trade in trades:
        pnl = float(trade.get("pnl", 0))
        balance += pnl

        if balance > peak:
            peak = balance

        drawdown = peak - balance
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return round(max_drawdown, 2)

def calculate_streaks(trades: List[Dict]) -> tuple:
    """Calculate maximum winning and losing streaks"""
    if not trades:
        return 0, 0

    current_win_streak = 0
    current_loss_streak = 0
    max_win_streak = 0
    max_loss_streak = 0

    for trade in trades:
        pnl = float(trade.get("pnl", 0))

        if pnl > 0:  # Winner
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        elif pnl < 0:  # Loser
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)
        else:  # Breakeven - reset both
            current_win_streak = 0
            current_loss_streak = 0

    return max_win_streak, max_loss_streak

def calculate_monthly_performance(trades: List[Dict]) -> List[Dict]:
    """Group trades by month and calculate performance"""
    monthly_data = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "breakeven": 0, "pnl": 0.0})

    for trade in trades:
        date_str = trade.get("entry_date", "")
        if not date_str:
            continue

        # Parse date - handle various formats
        try:
            if isinstance(date_str, str):
                # Try to extract YYYY-MM
                if len(date_str) >= 7:
                    month_key = date_str[:7]  # YYYY-MM
                    year = int(date_str[:4])
                    month_name = datetime.strptime(date_str[5:7], "%m").strftime("%B")
                else:
                    continue
            else:
                continue
        except:
            continue

        pnl = float(trade.get("pnl", 0))
        monthly_data[month_key]["trades"] += 1
        monthly_data[month_key]["pnl"] += pnl

        if pnl > 0:
            monthly_data[month_key]["wins"] += 1
        elif pnl < 0:
            monthly_data[month_key]["losses"] += 1
        else:
            monthly_data[month_key]["breakeven"] += 1

    # Convert to list and calculate win rates
    result = []
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        win_rate = safe_div(data["wins"], data["trades"] - data["breakeven"], 0) * 100

        result.append({
            "month": month_key,
            "year": int(month_key[:4]),
            "month_name": datetime.strptime(month_key[5:7], "%m").strftime("%B"),
            "trades": data["trades"],
            "wins": data["wins"],
            "losses": data["losses"],
            "breakeven": data["breakeven"],
            "pnl": round(data["pnl"], 2),
            "win_rate": round(win_rate, 2)
        })

    return result

def calculate_risk_consistency(trades: List[Dict]) -> float:
    """Calculate risk consistency score based on position size variation"""
    if len(trades) < 2:
        return 100.0

    # Extract position sizes (volume/lots)
    sizes = []
    for trade in trades:
        volume = float(trade.get("volume", 0))
        if volume > 0:
            sizes.append(volume)

    if len(sizes) < 2:
        return 100.0

    # Calculate coefficient of variation (CV)
    try:
        mean_size = statistics.mean(sizes)
        stdev_size = statistics.stdev(sizes)
        cv = stdev_size / mean_size if mean_size > 0 else 0

        # Convert to score (lower CV = higher score)
        score = max(0, min(100, 100 - (cv * 100)))
        return round(score, 2)
    except:
        return 50.0

def detect_strategy(trades: List[Dict]) -> str:
    """Detect trading strategy based on trade characteristics"""
    if not trades:
        return "Unknown"

    # Calculate average holding time if entry/exit dates available
    durations = []
    for trade in trades:
        entry = trade.get("entry_date", "")
        exit = trade.get("exit_date", "")
        if entry and exit:
            try:
                # Simple check - if same day, likely scalping
                if entry[:10] == exit[:10]:
                    durations.append("short")
                else:
                    durations.append("long")
            except:
                pass

    short_ratio = safe_div(durations.count("short"), len(durations), 0)

    # Calculate win rate
    wins = sum(1 for t in trades if float(t.get("pnl", 0)) > 0)
    win_rate = safe_div(wins, len(trades), 0) * 100

    # Strategy detection logic
    if short_ratio > 0.7:
        if win_rate > 55:
            return "Scalping (High Frequency)"
        else:
            return "Day Trading"
    elif short_ratio > 0.3:
        return "Swing Trading"
    else:
        return "Position Trading"

def calculate_trade_distribution(trades: List[Dict]) -> Dict:
    """Calculate wins/losses/breakeven distribution"""
    wins = sum(1 for t in trades if float(t.get("pnl", 0)) > 0)
    losses = sum(1 for t in trades if float(t.get("pnl", 0)) < 0)
    breakeven = sum(1 for t in trades if float(t.get("pnl", 0)) == 0)

    return {
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven
    }

def calculate_performance_metrics(trades: List[Dict]) -> Dict:
    """Calculate comprehensive performance metrics"""
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "loss_rate": 0.0,
            "profit_factor": 0.0,
            "total_pnl": 0.0,
            "net_pnl": 0.0,
            "average_pnl": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "max_drawdown": 0.0,
            "expectancy": 0.0,
            "winning_streak": 0,
            "losing_streak": 0
        }

    total_trades = len(trades)
    pnls = [float(t.get("pnl", 0)) for t in trades]

    winning_trades = [p for p in pnls if p > 0]
    losing_trades = [p for p in pnls if p < 0]
    breakeven_trades = [p for p in pnls if p == 0]

    total_profit = sum(winning_trades) if winning_trades else 0
    total_loss = abs(sum(losing_trades)) if losing_trades else 0

    # Win/loss rates (excluding breakeven from denominator)
    decisive_trades = len(winning_trades) + len(losing_trades)
    win_rate = safe_div(len(winning_trades), decisive_trades, 0) * 100
    loss_rate = 100 - win_rate

    # Profit factor (fixed - no infinity)
    if total_loss == 0:
        profit_factor = min(total_profit, 999.99) if total_profit > 0 else 0.0
    else:
        profit_factor = min(safe_div(total_profit, total_loss, 0), 999.99)

    # Expectancy (correct formula)
    avg_win = safe_div(sum(winning_trades), len(winning_trades), 0)
    avg_loss = safe_div(sum(losing_trades), len(losing_trades), 0)
    expectancy = (win_rate/100 * avg_win) - (loss_rate/100 * abs(avg_loss))

    # Streaks
    winning_streak, losing_streak = calculate_streaks(trades)

    # Max drawdown
    max_drawdown = calculate_max_drawdown(trades)

    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "breakeven_trades": len(breakeven_trades),
        "win_rate": round(win_rate, 2),
        "loss_rate": round(loss_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "total_pnl": round(sum(pnls), 2),
        "net_pnl": round(sum(pnls), 2),
        "average_pnl": round(safe_div(sum(pnls), len(pnls), 0), 2),
        "average_win": round(avg_win, 2),
        "average_loss": round(avg_loss, 2),
        "max_drawdown": round(max_drawdown, 2),
        "expectancy": round(expectancy, 2),
        "winning_streak": winning_streak,
        "losing_streak": losing_streak
    }

async def analyze_with_ai_coach(trades: List[Dict], stats: Dict) -> Dict:
    """AI Trading Coach - analyze performance and provide insights"""

    if not OPENROUTER_CONFIGURED:
        # Fallback analysis
        return generate_fallback_coach_analysis(trades, stats)

    try:
        # Prepare summary for AI
        summary = f"""
        Trading Performance Summary:
        - Total Trades: {stats['total_trades']}
        - Win Rate: {stats['win_rate']}%
        - Profit Factor: {stats['profit_factor']}
        - Net P&L: ${stats['net_pnl']}
        - Expectancy: ${stats['expectancy']}
        - Max Drawdown: ${stats['max_drawdown']}
        - Winning Streak: {stats['winning_streak']}
        - Losing Streak: {stats['losing_streak']}
        - Average Win: ${stats['average_win']}
        - Average Loss: ${stats['average_loss']}
        """

        system_prompt = """You are an expert trading coach and performance analyst. 
        Analyze the trader's performance data and identify patterns, mistakes, and strengths.

        Focus on detecting:
        1. Overtrading (high frequency, low quality)
        2. Revenge trading (increasing size after losses)
        3. FOMO trading (chasing moves, poor entries)
        4. Poor risk management (inconsistent position sizing)
        5. Strategy inconsistency (deviating from plan)

        Return STRICT JSON format:
        {
            "discipline_score": 0-100,
            "risk_management_score": 0-100,
            "strategy_consistency": 0-100,
            "main_mistake": "description of primary issue",
            "recommendation": "specific actionable advice",
            "detected_patterns": ["pattern1", "pattern2"],
            "strengths": ["strength1", "strength2"],
            "improvements": ["improvement1", "improvement2"]
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
                        {"role": "user", "content": f"Analyze this trader:\n{summary}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1200
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception("AI service unavailable")

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON response
            try:
                json_match = re.search(r"{.*}", content, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group())
                else:
                    ai_data = json.loads(content)

                ai_data["mode"] = "ai"
                return ai_data
            except:
                return generate_fallback_coach_analysis(trades, stats)

    except Exception as e:
        print(f"[AI Coach Error] {e}", flush=True)
        return generate_fallback_coach_analysis(trades, stats)

def generate_fallback_coach_analysis(trades: List[Dict], stats: Dict) -> Dict:
    """Generate AI coach analysis without AI service"""

    patterns = []
    strengths = []
    improvements = []

    # Detect patterns
    if stats['profit_factor'] > 2:
        strengths.append("Strong profit factor indicates good risk management")
    elif stats['profit_factor'] < 1:
        patterns.append("Losing strategy - review approach")
        improvements.append("Focus on improving win rate or risk:reward ratio")

    if stats['win_rate'] > 55:
        strengths.append("Good win rate shows consistent strategy execution")
    elif stats['win_rate'] < 40:
        patterns.append("Low win rate suggests entry timing issues")
        improvements.append("Work on entry criteria and patience")

    if stats['losing_streak'] > 5:
        patterns.append("Long losing streaks detected - possible revenge trading")
        improvements.append("Implement mandatory break after 3 consecutive losses")

    if stats['max_drawdown'] > stats['net_pnl'] * 0.5:
        patterns.append("Large drawdowns relative to gains")
        improvements.append("Reduce position sizes and tighten stop losses")

    if stats['expectancy'] < 0:
        patterns.append("Negative expectancy - unsustainable long-term")
        improvements.append("Revise trading strategy completely")

    if not strengths:
        strengths.append("Trading consistently - foundation for improvement")

    if not improvements:
        improvements.append("Maintain current discipline and consistency")

    # Calculate scores
    discipline_score = min(100, max(20, int(stats['win_rate'])))
    risk_score = min(100, max(20, int(stats['profit_factor'] * 30)))
    consistency_score = min(100, max(20, 100 - stats['losing_streak'] * 10))

    # Main mistake
    if patterns:
        main_mistake = patterns[0]
    elif stats['win_rate'] < 50:
        main_mistake = "Win rate below 50% - review entry criteria"
    else:
        main_mistake = "No major mistakes detected - focus on consistency"

    return {
        "discipline_score": discipline_score,
        "risk_management_score": risk_score,
        "strategy_consistency": consistency_score,
        "main_mistake": main_mistake,
        "recommendation": improvements[0] if improvements else "Keep maintaining your trading journal",
        "detected_patterns": patterns,
        "strengths": strengths,
        "improvements": improvements,
        "mode": "fallback"
    }

def calculate_overall_grade(stats: Dict) -> tuple:
    """Calculate overall grade and score"""
    score = 0

    if stats['win_rate'] > 50:
        score += 25
    if stats['win_rate'] > 60:
        score += 10
    if stats['profit_factor'] > 1.5:
        score += 25
    if stats['profit_factor'] > 2.0:
        score += 10
    if stats['expectancy'] > 0:
        score += 20
    if stats['total_trades'] > 10:
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

    return grade, score

# ==========================================
# API ENDPOINTS
# ==========================================

@router.post("/analyze-journal", response_model=PerformanceResponse)
async def analyze_journal(
    request: Dict,
    current_user = Depends(get_current_user)
):
    """
    Analyze trading journal with comprehensive analytics and AI coaching.
    """
    user_id   = current_user.get("id") if current_user else None
    user_tier = current_user.get("subscription_tier", "free") if current_user else "free"

    if user_id and not await check_limit(user_id, user_tier, "performance_analysis"):
        raise HTTPException(
            status_code=402,
            detail={
                "feature": "performance_analysis",
                "message": "Monthly performance analysis limit reached. Upgrade to Pro for unlimited.",
                "upgrade": True,
            }
        )

    try:
        trades = request.get("trades", [])

        if not trades:
            raise HTTPException(400, "No trades provided")

        # Calculate all metrics
        stats = calculate_performance_metrics(trades)
        equity_curve = calculate_equity_curve(trades)
        trade_distribution = calculate_trade_distribution(trades)
        monthly_performance = calculate_monthly_performance(trades)
        risk_consistency = calculate_risk_consistency(trades)
        detected_strategy = detect_strategy(trades)

        # AI Coach analysis
        ai_coach = await analyze_with_ai_coach(trades, stats)

        # Overall grade
        grade, score = calculate_overall_grade(stats)

        if user_id:
            await log_usage(user_id, "performance_analysis")

        return {
            "total_trades": stats["total_trades"],
            "win_rate": stats["win_rate"],
            "profit_factor": stats["profit_factor"],
            "net_pnl": stats["net_pnl"],
            "expectancy": stats["expectancy"],
            "max_drawdown": stats["max_drawdown"],
            "winning_streak": stats["winning_streak"],
            "losing_streak": stats["losing_streak"],
            "equity_curve": equity_curve,
            "trade_distribution": trade_distribution,
            "monthly_performance": monthly_performance,
            "ai_coach": ai_coach,
            "risk_consistency_score": risk_consistency,
            "detected_strategy": detected_strategy,
            "overall_grade": grade,
            "overall_score": score
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ANALYZE ERROR] {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/upload-journal")
async def upload_journal(
    file: UploadFile = File(...),
    format: str = Form("auto"),
    current_user = Depends(get_current_user)
):
    """
    Upload and parse trade journal file with full analytics.
    """
    user_id   = current_user.get("id") if current_user else None
    user_tier = current_user.get("subscription_tier", "free") if current_user else "free"

    if user_id and not await check_limit(user_id, user_tier, "performance_analysis"):
        raise HTTPException(
            status_code=402,
            detail={
                "feature": "performance_analysis",
                "message": "Monthly performance analysis limit reached. Upgrade to Pro for unlimited.",
                "upgrade": True,
            }
        )

    try:
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(400, "Empty file uploaded")

        # Parse file
        trades = TradeJournalParser.parse_file(content, file.filename, format)

        if not trades:
            raise HTTPException(400, "No trades found in file")

        # Run full analysis
        stats = calculate_performance_metrics(trades)
        equity_curve = calculate_equity_curve(trades)
        trade_distribution = calculate_trade_distribution(trades)
        monthly_performance = calculate_monthly_performance(trades)
        risk_consistency = calculate_risk_consistency(trades)
        detected_strategy = detect_strategy(trades)

        # AI Coach
        ai_coach = await analyze_with_ai_coach(trades, stats)

        # Grade
        grade, score = calculate_overall_grade(stats)

        if user_id:
            await log_usage(user_id, "performance_analysis", filename=file.filename or "")

        return {
            "trades": trades[:50],  # Limit for response size
            "statistics": {
                "total_trades": stats["total_trades"],
                "win_rate": stats["win_rate"],
                "profit_factor": stats["profit_factor"],
                "net_pnl": stats["net_pnl"],
                "expectancy": stats["expectancy"],
                "max_drawdown": stats["max_drawdown"],
                "winning_streak": stats["winning_streak"],
                "losing_streak": stats["losing_streak"]
            },
            "equity_curve": equity_curve,
            "trade_distribution": trade_distribution,
            "monthly_performance": monthly_performance,
            "ai_coach": ai_coach,
            "risk_consistency_score": risk_consistency,
            "detected_strategy": detected_strategy,
            "overall_grade": grade,
            "overall_score": score
        }

    except ValueError as e:
        raise HTTPException(400, f"Parse error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}", flush=True)
        raise HTTPException(500, f"Failed to process file: {str(e)}")
