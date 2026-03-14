"""
AI Trading Mentor - PRODUCTION READY
Standardized to use OpenRouter API only
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import os
import httpx

from .security import get_current_user

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

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
    AI Mentor using OpenRouter (Claude/GPT via OpenRouter).
    Returns 503 if OpenRouter is not configured.
    """
    if not OPENROUTER_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail="AI Mentor service not configured. Please set OPENROUTER_API_KEY environment variable."
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
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"[AI MENTOR ERROR] OpenRouter HTTP {response.status_code}: {response.text}", flush=True)
                if response.status_code == 401:
                    raise HTTPException(status_code=503, detail="AI authentication failed. Check API key.")
                elif response.status_code == 429:
                    raise HTTPException(status_code=503, detail="AI service rate limited. Please try again.")
                else:
                    raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
            
            data = response.json()
            
            if "choices" not in data or len(data["choices"]) == 0:
                raise HTTPException(status_code=503, detail="Invalid AI response format")
            
            content = data["choices"][0]["message"]["content"]
            
            # Generate resources based on topic (maintain compatibility)
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
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI request timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI MENTOR ERROR] {e}", flush=True)
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

@router.post("/review-trade")
async def review_trade(
    trade: TradeReviewRequest,
    current_user = Depends(get_current_user)
):
    """Production trade review using OpenRouter"""
    if not OPENROUTER_CONFIGURED:
        raise HTTPException(status_code=503, detail="AI service not configured. Set OPENROUTER_API_KEY.")
    
    try:
        pnl = (trade.exit_price - trade.entry_price) if trade.direction.upper() == "BUY" else (trade.entry_price - trade.exit_price)
        risk = abs(trade.entry_price - trade.stop_loss)
        reward = abs(trade.take_profit - trade.entry_price)
        r_multiple = pnl / risk if risk > 0 else 0
        
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
                    "messages": [{"role": "user", "content": analysis_prompt}],
                    "max_tokens": 400,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="AI analysis failed")
            
            data = response.json()
            ai_content = data["choices"][0]["message"]["content"]
            
            return {
                "trade_analysis": ai_content,
                "metrics": {
                    "r_multiple": round(r_multiple, 2),
                    "risk_reward": round(reward/risk, 2) if risk > 0 else 0,
                    "pnl": round(pnl, 2)
                }
            }
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Analysis timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TRADE REVIEW ERROR] {e}", flush=True)
        raise HTTPException(status_code=503, detail=f"Analysis failed: {str(e)}")

@router.get("/daily-wisdom")
async def daily_trading_wisdom():
    """Returns trading wisdom"""
    import random
    
    wisdoms = [
        {"quote": "Cut losses short, let profits run", "author": "Jesse Livermore"},
        {"quote": "Risk comes from not knowing what you're doing", "author": "Warren Buffett"},
        {"quote": "The market can stay irrational longer than you can stay solvent", "author": "Keynes"}
    ]
    
    return random.choice(wisdoms)
