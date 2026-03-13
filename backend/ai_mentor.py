"""
AI Trading Mentor - Personalized Coaching System
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import os
import json
from openai import AsyncOpenAI

from .security import get_current_user
from .database import database

router = APIRouter(prefix="", tags=["ai-mentor"])

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

class MentorQuery(BaseModel):
    question: str
    context: Optional[str] = Field(None, description="Additional trading context")
    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    topic: Optional[str] = Field(None, description="Specific topic: risk_management, technical_analysis, psychology, strategy")

class LearningPathRequest(BaseModel):
    goal: str = Field(..., description="Trading goal: consistent_profits, risk_management, scalping, swing_trading")
    current_level: Literal["beginner", "intermediate", "advanced"]
    time_available: str = Field(..., description="Hours per week: 5, 10, 20+")
    preferred_markets: List[str] = ["forex"]

class TradeReviewRequest(BaseModel):
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    direction: str
    outcome: Literal["win", "loss", "breakeven"]
    notes: Optional[str] = None
    emotion_state: Optional[str] = None  # confident, fearful, greedy, revenge

@router.post("/ask")
async def ask_mentor(
    query: MentorQuery,
    current_user = Depends(get_current_user)
):
    """
    Ask the AI trading mentor a question. Get personalized coaching.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "response": f"[Demo Mode] As a {query.skill_level} trader, regarding '{query.question}': Focus on risk management first. Always use stop losses and never risk more than 1-2% per trade. Would you like specific strategies for {query.topic or 'general trading'}?",
            "suggested_resources": ["Risk Management Basics", "Position Sizing Guide"],
            "follow_up_questions": ["How do I calculate position size?", "What's a good risk/reward ratio?"],
            "mentor_tone": "encouraging"
        }
    
    system_prompt = f"""You are an expert trading mentor coaching a {query.skill_level} level trader. 
    Be encouraging but realistic about trading challenges. 
    Focus on: 1) Risk management 2) Psychology 3) Strategy refinement
    Keep responses concise (max 3 paragraphs) and actionable."""
    
    user_prompt = f"""
    Question: {query.question}
    Topic: {query.topic or 'general'}
    Context: {query.context or 'No additional context'}
    
    Provide specific, actionable advice. Include 2-3 follow-up questions to deepen understanding.
    """
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        
        # Generate follow-up questions
        follow_ups = await _generate_followups(query.question, query.topic)
        
        # Suggest resources
        resources = await _suggest_resources(query.topic, query.skill_level)
        
        return {
            "response": content,
            "suggested_resources": resources,
            "follow_up_questions": follow_ups,
            "mentor_tone": "encouraging" if "beginner" in query.skill_level else "analytical",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(500, f"Mentor service error: {str(e)}")

@router.post("/learning-path")
async def generate_learning_path(
    request: LearningPathRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate a personalized learning path based on goals and availability.
    """
    paths = {
        "beginner": {
            "weeks": 12,
            "phases": [
                {"weeks": "1-3", "focus": "Foundation", "topics": ["Market basics", "Order types", "Risk management"], "tasks": ["Open demo account", "Place 10 demo trades"]},
                {"weeks": "4-6", "focus": "Technical Analysis", "topics": ["Support/Resistance", "Trend lines", "Candlestick patterns"], "tasks": ["Identify 20 support/resistance levels"]},
                {"weeks": "7-9", "focus": "Strategy Development", "topics": ["Backtesting", "Journaling", "Entry/Exit rules"], "tasks": ["Create trading plan", "Backtest 50 trades"]},
                {"weeks": "10-12", "focus": "Psychology & Live Trading", "topics": ["Emotion control", "Position sizing", "Review process"], "tasks": ["Start with micro lots", "Weekly reviews"]}
            ]
        },
        "intermediate": {
            "weeks": 8,
            "phases": [
                {"weeks": "1-2", "focus": "Advanced Patterns", "topics": ["Harmonic patterns", "Elliott Wave basics", "Multi-timeframe"], "tasks": ["Identify 5 harmonic setups"]},
                {"weeks": "3-4", "focus": "Risk Management Mastery", "topics": ["Portfolio heat", "Correlation", "Drawdown recovery"], "tasks": ["Calculate max portfolio risk"]},
                {"weeks": "5-6", "focus": "Strategy Optimization", "topics": ["Win rate vs R:R", "Expectancy", "Market regimes"], "tasks": ["Analyze 100 trade sample"]},
                {"weeks": "7-8", "focus": "Consistency", "topics": ["Routine building", "Mental game", "Advanced journaling"], "tasks": ["30-day consistency challenge"]}
            ]
        },
        "advanced": {
            "weeks": 6,
            "phases": [
                {"weeks": "1-2", "focus": "Market Microstructure", "topics": ["Order flow", "Liquidity", "Algorithmic trading"], "tasks": ["Analyze order book depth"]},
                {"weeks": "3-4", "focus": "Portfolio Management", "topics": ["Asset allocation", "Hedging", "Drawdown control"], "tasks": ["Build correlation matrix"]},
                {"weeks": "5-6", "focus": "System Automation", "topics": ["EA development", "API trading", "Risk automation"], "tasks": ["Automate one strategy component"]}
            ]
        }
    }
    
    level_path = paths.get(request.current_level, paths["beginner"])
    
    # Customize based on time available
    time_multiplier = 1.0 if request.time_available == "10" else 0.7 if request.time_available == "5" else 1.3
    
    return {
        "goal": request.goal,
        "current_level": request.current_level,
        "duration_weeks": int(level_path["weeks"] * time_multiplier),
        "weekly_time_commitment": request.time_available,
        "phases": level_path["phases"],
        "recommended_markets": request.preferred_markets,
        "success_metrics": [
            "Consistent risk management (no >2% losses)",
            "Positive expectancy after 50 trades",
            "Emotional control (no revenge trading)"
        ],
        "milestones": [
            {"week": 4, "achievement": "Complete foundation"},
            {"week": 8, "achievement": "First profitable month"},
            {"week": 12, "achievement": "Consistent execution"}
        ]
    }

@router.post("/review-trade")
async def review_trade(
    trade: TradeReviewRequest,
    current_user = Depends(get_current_user)
):
    """
    AI review of a specific trade with psychology and technical feedback.
    """
    pnl = (trade.exit_price - trade.entry_price) if trade.direction == "BUY" else (trade.entry_price - trade.exit_price)
    risk = abs(trade.entry_price - trade.stop_loss)
    reward = abs(trade.take_profit - trade.entry_price)
    r_multiple = pnl / risk if risk > 0 else 0
    
    review = {
        "trade_id": f"review_{datetime.utcnow().timestamp()}",
        "technical_score": 0,
        "psychology_score": 0,
        "overall_grade": "",
        "feedback": [],
        "psychology_insights": [],
        "improvements": []
    }
    
    # Technical Analysis
    if reward / risk >= 2.0:
        review["technical_score"] += 30
        review["feedback"].append("✓ Excellent R:R ratio (2:1 or better)")
    elif reward / risk >= 1.5:
        review["technical_score"] += 20
        review["feedback"].append("~ Good R:R ratio")
    else:
        review["feedback"].append("✗ R:R below 1.5 - consider better setups")
    
    if trade.stop_loss < trade.entry_price and trade.direction == "BUY":
        review["technical_score"] += 20
        review["feedback"].append("✓ Logical stop placement")
    
    # Outcome analysis
    if trade.outcome == "win" and r_multiple >= 2:
        review["technical_score"] += 30
        review["feedback"].append("✓ Excellent trade management - let winners run")
    elif trade.outcome == "loss" and abs(r_multiple) <= 1:
        review["technical_score"] += 20
        review["feedback"].append("✓ Good loss control - kept within 1R")
    elif trade.outcome == "loss" and abs(r_multiple) > 2:
        review["feedback"].append("✗ Failed to cut loss - consider tighter stops")
    
    # Psychology Analysis
    emotion_scores = {
        "confident": 25,
        "neutral": 20,
        "apprehensive": 15,
        "fearful": 10,
        "greedy": 5,
        "revenge": 0
    }
    
    review["psychology_score"] = emotion_scores.get(trade.emotion_state, 15)
    
    if trade.emotion_state in ["revenge", "greedy"]:
        review["psychology_insights"].append("⚠ Emotional trading detected - take a break")
    elif trade.emotion_state == "fearful":
        review["psychology_insights"].append("~ Fear may be causing premature exits")
    
    if trade.outcome == "win" and trade.emotion_state == "greedy":
        review["psychology_insights"].append("⚠ Don't let wins feed overconfidence")
    
    # Calculate overall grade
    total_score = review["technical_score"] + review["psychology_score"]
    if total_score >= 80:
        review["overall_grade"] = "A (Excellent)"
    elif total_score >= 60:
        review["overall_grade"] = "B (Good)"
    elif total_score >= 40:
        review["overall_grade"] = "C (Average)"
    else:
        review["overall_grade"] = "D (Needs Improvement)"
    
    review["improvements"] = [
        "Focus on 2:1 R:R minimum setups",
        "Journal emotions before each trade",
        "Review chart after entry to confirm logic"
    ]
    
    return review

@router.get("/daily-wisdom")
async def daily_trading_wisdom(current_user = Depends(get_current_user)):
    """
    Get daily trading tip or quote.
    """
    import random
    wisdoms = [
        {"quote": "Cut losses short, let profits run", "author": "Jesse Livermore", "theme": "risk_management"},
        {"quote": "The market can stay irrational longer than you can stay solvent", "author": "John Maynard Keynes", "theme": "patience"},
        {"quote": "Plan the trade, trade the plan", "author": "Unknown", "theme": "discipline"},
        {"quote": "Risk comes from not knowing what you're doing", "author": "Warren Buffett", "theme": "education"},
        {"quote": "The goal is not to be right, but to make money", "author": "Unknown", "theme": "psychology"}
    ]
    
    return random.choice(wisdoms)

async def _generate_followups(question: str, topic: Optional[str]) -> List[str]:
    """Generate relevant follow-up questions."""
    return [
        f"How does this apply to current market conditions?",
        f"What risk management rules should I pair with this?",
        f"Can you give me a specific example of {topic or 'this strategy'}?"
    ]

async def _suggest_resources(topic: Optional[str], level: str) -> List[str]:
    """Suggest learning resources."""
    resources = {
        "risk_management": ["Position Sizing Calculator", "The 1% Rule Explained"],
        "technical_analysis": ["Support/Resistance Masterclass", "Indicator Guide"],
        "psychology": ["Trading in the Zone Summary", "Emotion Control Techniques"],
        "strategy": ["Backtesting 101", "Building a Trading Plan"]
    }
    return resources.get(topic, ["Trading Basics", "Risk Management Fundamentals"])
