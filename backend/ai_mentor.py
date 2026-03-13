"""
AI Trading Mentor - PRODUCTION READY
Requires OPENAI_API_KEY environment variable
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import os

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .security import get_current_user

router = APIRouter()

# Initialize client
client = None
api_key = os.getenv("OPENAI_API_KEY")
if OPENAI_AVAILABLE and api_key:
    client = AsyncOpenAI(api_key=api_key)

class MentorQuery(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = Field(None, max_length=1000)
    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    topic: Optional[str] = None

class TradeReviewRequest(BaseModel):
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    direction: str
    outcome: Literal["win", "loss", "breakeven"]
    notes: Optional[str] = None
    emotion_state: Optional[str] = None

@router.post("/ask")
async def ask_mentor(
    query: MentorQuery,
    current_user = Depends(get_current_user)
):
    """
    Production AI Mentor - Requires OpenAI API key
    Returns error if not configured rather than demo response
    """
    if not client:
        raise HTTPException(
            status_code=503,
            detail="AI Mentor service not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        system_prompt = f"""You are an expert trading mentor coaching a {query.skill_level} level trader. 
        Be encouraging but realistic about trading challenges. 
        Focus on: 1) Risk management 2) Psychology 3) Strategy refinement
        Keep responses concise (max 3 paragraphs) and actionable."""
        
        user_prompt = f"""
        Question: {query.question}
        Topic: {query.topic or 'general'}
        Context: {query.context or 'No additional context'}
        """
        
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
        
        # Generate resources based on topic
        resources = []
        if "risk" in query.question.lower() or query.topic == "risk_management":
            resources = ["Position Sizing Calculator", "Risk Management Guide"]
        elif "psychology" in query.question.lower() or query.topic == "psychology":
            resources = ["Trading Psychology Workbook", "Emotion Control Techniques"]
        elif "technical" in query.question.lower() or query.topic == "technical_analysis":
            resources = ["Chart Patterns Library", "Support/Resistance Masterclass"]
        else:
            resources = ["Trading Basics", "Risk Management Fundamentals"]
        
        return {
            "response": content,
            "suggested_resources": resources,
            "follow_up_questions": [
                "How do I calculate position size for this setup?",
                "What risk management rules should I apply?",
                "Can you give me a specific example?"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"[AI ERROR] {e}", flush=True)
        raise HTTPException(500, f"AI service error: {str(e)}")

@router.post("/review-trade")
async def review_trade(
    trade: TradeReviewRequest,
    current_user = Depends(get_current_user)
):
    """Production trade review with real calculations"""
    if not client:
        raise HTTPException(503, "AI service not configured")
    
    try:
        pnl = (trade.exit_price - trade.entry_price) if trade.direction.upper() == "BUY" else (trade.entry_price - trade.exit_price)
        risk = abs(trade.entry_price - trade.stop_loss)
        reward = abs(trade.take_profit - trade.entry_price)
        r_multiple = pnl / risk if risk > 0 else 0
        
        # AI analysis
        analysis_prompt = f"""
        Review this trade:
        Direction: {trade.direction}
        Entry: {trade.entry_price}, Exit: {trade.exit_price}
        Stop: {trade.stop_loss}, Target: {trade.take_profit}
        PnL: {pnl}, R-Multiple: {r_multiple:.2f}
        Outcome: {trade.outcome}
        Emotion: {trade.emotion_state or 'Not specified'}
        Notes: {trade.notes or 'None'}
        
        Provide brief technical and psychological feedback.
        """
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=400
        )
        
        return {
            "trade_analysis": response.choices[0].message.content,
            "metrics": {
                "r_multiple": round(r_multiple, 2),
                "risk_reward": round(reward/risk, 2) if risk > 0 else 0,
                "pnl": round(pnl, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.get("/daily-wisdom")
async def daily_trading_wisdom():
    """Returns trading wisdom - can use AI or database"""
    import random
    
    # Production: Could fetch from database or use AI
    wisdoms = [
        {"quote": "Cut losses short, let profits run", "author": "Jesse Livermore"},
        {"quote": "Risk comes from not knowing what you're doing", "author": "Warren Buffett"},
        {"quote": "The market can stay irrational longer than you can stay solvent", "author": "Keynes"}
    ]
    
    return random.choice(wisdoms)
