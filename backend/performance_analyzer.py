"""
Performance Analyzer - Trading Journal Insights & Psychology
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from statistics import mean, stdev
import math

from .security import get_current_user
from .database import database

router = APIRouter(prefix="", tags=["performance"])

class TradeEntry(BaseModel):
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    direction: str  # BUY or SELL
    entry_price: float
    exit_price: Optional[float]
    stop_loss: float
    take_profit: float
    position_size: float
    pnl: Optional[float]
    outcome: Optional[str]  # win, loss, breakeven
    tags: List[str] = []
    notes: Optional[str] = None
    emotion_before: Optional[str] = None
    emotion_after: Optional[str] = None

class PerformanceReport(BaseModel):
    total_trades: int
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    expectancy: float
    r_multiple_average: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    recovery_factor: float
    sharpe_ratio: Optional[float]

@router.post("/analyze-journal")
async def analyze_trading_journal(
    trades: List[TradeEntry],
    current_user = Depends(get_current_user)
):
    """
    Comprehensive analysis of trading journal with psychology insights.
    """
    if not trades:
        return {"error": "No trades provided"}
    
    analysis = {
        "statistics": {},
        "psychology": {},
        "patterns": {},
        "improvements": []
    }
    
    # Basic Statistics
    total = len(trades)
    wins = [t for t in trades if t.outcome == "win"]
    losses = [t for t in trades if t.outcome == "loss"]
    break_even = [t for t in trades if t.outcome == "breakeven"]
    
    win_count = len(wins)
    loss_count = len(losses)
    
    analysis["statistics"] = {
        "total_trades": total,
        "winning_trades": win_count,
        "losing_trades": loss_count,
        "break_even": len(break_even),
        "win_rate": round(win_count / total * 100, 2) if total > 0 else 0,
        "gross_profit": sum(t.pnl for t in wins if t.pnl),
        "gross_loss": abs(sum(t.pnl for t in losses if t.pnl)),
    }
    
    # Advanced Metrics
    win_pnls = [t.pnl for t in wins if t.pnl]
    loss_pnls = [abs(t.pnl) for t in losses if t.pnl]
    
    if win_pnls and loss_pnls:
        avg_win = mean(win_pnls)
        avg_loss = mean(loss_pnls)
        
        analysis["statistics"].update({
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
            "profit_factor": round(sum(win_pnls) / sum(loss_pnls), 2) if sum(loss_pnls) > 0 else float('inf'),
            "expectancy": round((analysis["statistics"]["win_rate"]/100 * avg_win) - ((1-analysis["statistics"]["win_rate"]/100) * avg_loss), 2),
            "payoff_ratio": round(avg_win / avg_loss, 2) if avg_loss > 0 else 0
        })
    
    # R-Multiple Analysis
    r_multiples = []
    for trade in trades:
        if trade.pnl and trade.entry_price and trade.stop_loss:
            risk = abs(trade.entry_price - trade.stop_loss)
            if risk > 0:
                r = trade.pnl / risk
                r_multiples.append(r)
    
    if r_multiples:
        analysis["statistics"]["r_multiple_average"] = round(mean(r_multiples), 2)
        analysis["statistics"]["r_multiple_std"] = round(stdev(r_multiples), 2) if len(r_multiples) > 1 else 0
    
    # Psychology Analysis
    emotion_wins = {}
    emotion_losses = {}
    
    for trade in trades:
        emotion = trade.emotion_before or "unknown"
        if trade.outcome == "win":
            emotion_wins[emotion] = emotion_wins.get(emotion, 0) + 1
        else:
            emotion_losses[emotion] = emotion_losses.get(emotion, 0) + 1
    
    analysis["psychology"] = {
        "best_trading_state": max(emotion_wins, key=emotion_wins.get) if emotion_wins else "unknown",
        "worst_trading_state": max(emotion_losses, key=emotion_losses.get) if emotion_losses else "unknown",
        "emotional_consistency": "high" if len(set(t.emotion_before for t in trades)) < 3 else "low",
        "revenge_trading_detected": any("revenge" in (t.notes or "").lower() for t in trades),
        "fomo_trades": sum(1 for t in trades if "fomo" in (t.notes or "").lower() or "missed" in (t.notes or "").lower())
    }
    
    # Pattern Detection
    hour_performance = {}
    for trade in trades:
        if trade.pnl:
            hour = trade.entry_date.hour
            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(trade.pnl)
    
    best_hours = sorted(hour_performance.items(), 
                       key=lambda x: mean(x[1]) if x[1] else 0, 
                       reverse=True)[:3]
    
    analysis["patterns"] = {
        "best_trading_hours": [f"{h[0]}:00 (avg: ${mean(h[1]):.2f})" for h in best_hours],
        "symbol_performance": _analyze_by_symbol(trades),
        "tag_performance": _analyze_by_tags(trades),
        "day_of_week": _analyze_by_day(trades),
        "consecutive_analysis": _analyze_streaks(trades)
    }
    
    # Improvement Suggestions
    analysis["improvements"] = _generate_improvements(analysis, trades)
    
    # Grade
    overall_score = _calculate_overall_grade(analysis)
    analysis["overall_grade"] = overall_score["grade"]
    analysis["overall_score"] = overall_score["score"]
    analysis["next_milestone"] = overall_score["next_goal"]
    
    return analysis

def _analyze_by_symbol(trades: List[TradeEntry]) -> Dict:
    """Analyze performance by symbol."""
    symbols = {}
    for trade in trades:
        if trade.symbol not in symbols:
            symbols[trade.symbol] = {"wins": 0, "losses": 0, "pnl": 0}
        
        if trade.outcome == "win":
            symbols[trade.symbol]["wins"] += 1
        elif trade.outcome == "loss":
            symbols[trade.symbol]["losses"] += 1
        
        if trade.pnl:
            symbols[trade.symbol]["pnl"] += trade.pnl
    
    return dict(sorted(symbols.items(), key=lambda x: x[1]["pnl"], reverse=True))

def _analyze_by_tags(trades: List[TradeEntry]) -> Dict:
    """Analyze which strategy tags perform best."""
    tags = {}
    for trade in trades:
        for tag in trade.tags:
            if tag not in tags:
                tags[tag] = {"wins": 0, "total": 0, "pnl": 0}
            
            tags[tag]["total"] += 1
            if trade.outcome == "win":
                tags[tag]["wins"] += 1
            if trade.pnl:
                tags[tag]["pnl"] += trade.pnl
    
    return {k: {**v, "win_rate": round(v['wins']/v['total']*100, 1)} 
            for k, v in sorted(tags.items(), key=lambda x: x[1]['pnl'], reverse=True)}

def _analyze_by_day(trades: List[TradeEntry]) -> Dict:
    """Analyze by day of week."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_stats = {day: {"trades": 0, "pnl": 0} for day in days}
    
    for trade in trades:
        if trade.entry_date:
            day = days[trade.entry_date.weekday()] if trade.entry_date.weekday() < 5 else "Weekend"
            if day in day_stats:
                day_stats[day]["trades"] += 1
                if trade.pnl:
                    day_stats[day]["pnl"] += trade.pnl
    
    return day_stats

def _analyze_streaks(trades: List[TradeEntry]) -> Dict:
    """Analyze winning/losing streaks."""
    if not trades:
        return {}
    
    current_streak = 1
    max_win_streak = 0
    max_loss_streak = 0
    current_type = trades[0].outcome
    
    for trade in trades[1:]:
        if trade.outcome == current_type and trade.outcome in ["win", "loss"]:
            current_streak += 1
        else:
            if current_type == "win":
                max_win_streak = max(max_win_streak, current_streak)
            elif current_type == "loss":
                max_loss_streak = max(max_loss_streak, current_streak)
            current_streak = 1
            current_type = trade.outcome
    
    # Check last streak
    if current_type == "win":
        max_win_streak = max(max_win_streak, current_streak)
    elif current_type == "loss":
        max_loss_streak = max(max_loss_streak, current_streak)
    
    return {
        "max_consecutive_wins": max_win_streak,
        "max_consecutive_losses": max_loss_streak,
        "current_streak": current_streak,
        "streak_type": current_type
    }

def _generate_improvements(analysis: Dict, trades: List[TradeEntry]) -> List[str]:
    """Generate actionable improvement suggestions."""
    suggestions = []
    stats = analysis["statistics"]
    psych = analysis["psychology"]
    
    if stats.get("win_rate", 0) < 40:
        suggestions.append("⚠️ Win rate below 40%. Focus on higher probability setups and avoid overtrading.")
    
    if stats.get("payoff_ratio", 0) < 1.5:
        suggestions.append("📉 Risk/Reward ratio needs improvement. Aim for minimum 1.5:1 on all trades.")
    
    if psych.get("revenge_trading_detected"):
        suggestions.append("🧠 Revenge trading detected. Implement mandatory cooling-off period after losses.")
    
    if psych.get("fomo_trades", 0) > 2:
        suggestions.append("⚡ FOMO trading pattern found. Stick to pre-defined watchlist and entry rules.")
    
    if stats.get("profit_factor", 0) < 1.5:
        suggestions.append("💰 Profit factor below 1.5. Review losing trades for common mistakes.")
    
    if analysis["patterns"].get("consecutive_analysis", {}).get("max_consecutive_losses", 0) > 4:
        suggestions.append("🛑 Risk management alert: You had 5+ consecutive losses. Reduce position size temporarily.")
    
    if not suggestions:
        suggestions.append("✅ Good performance! Focus on consistency and maintaining your edge.")
    
    return suggestions

def _calculate_overall_grade(analysis: Dict) -> Dict:
    """Calculate overall trading grade."""
    score = 0
    
    # Win rate (30 points)
    wr = analysis["statistics"].get("win_rate", 0)
    if wr >= 60: score += 30
    elif wr >= 50: score += 20
    elif wr >= 40: score += 10
    
    # Profit factor (30 points)
    pf = analysis["statistics"].get("profit_factor", 0)
    if pf >= 2.0: score += 30
    elif pf >= 1.5: score += 20
    elif pf >= 1.0: score += 10
    
    # R multiple (20 points)
    r = analysis["statistics"].get("r_multiple_average", 0)
    if r >= 2.0: score += 20
    elif r >= 1.0: score += 15
    elif r >= 0: score += 5
    
    # Psychology (20 points)
    if not analysis["psychology"].get("revenge_trading_detected"): score += 10
    if analysis["psychology"].get("emotional_consistency") == "high": score += 10
    
    # Grade
    if score >= 90: grade = "A+ (Elite Trader)"
    elif score >= 80: grade = "A (Excellent)"
    elif score >= 70: grade = "B (Good)"
    elif score >= 60: grade = "C (Average)"
    else: grade = "D (Needs Work)"
    
    # Next goal
    if score < 60:
        next_goal = "Focus on risk management - reduce position sizes"
    elif score < 70:
        next_goal = "Improve win rate by being more selective with setups"
    elif score < 80:
        next_goal = "Optimize R:R ratio by letting winners run longer"
    else:
        next_goal = "Maintain consistency and consider increasing size"
    
    return {"score": score, "grade": grade, "next_goal": next_goal}

@router.get("/dashboard-stats")
async def get_performance_dashboard(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """
    Get quick performance stats for dashboard.
    """
    # In production, fetch from database
    # For now, return structure
    
    return {
        "period": f"Last {days} days",
        "summary": {
            "trades_taken": 25,
            "win_rate": 56.0,
            "net_pnl": 1250.50,
            "best_trade": 450.00,
            "worst_trade": -200.00
        },
        "daily_equity_curve": [
            {"date": (datetime.now() - timedelta(days=i)).isoformat(), "equity": 10000 + (i * 50)}
            for i in range(days)
        ],
        "win_loss_distribution": {
            "wins": 14,
            "losses": 10,
            "breakeven": 1
        },
        "recent_activity": [
            {"date": datetime.now().isoformat(), "action": "Trade reviewed", "symbol": "EURUSD", "pnl": 120.00}
        ]
    }
