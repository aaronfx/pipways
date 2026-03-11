"""
AI Services Routes
Handles AI analysis and mentoring
"""
from fastapi import APIRouter, HTTPException, Depends
import os
from typing import Optional

from . import database
from .security import get_current_user, get_current_user_optional
from .schemas import AIAnalyzeRequest, AIMentorRequest

router = APIRouter()

# System prompt is hidden from frontend - stored only in backend
SYSTEM_PROMPT = """You are an expert trading mentor. Provide clear, actionable advice about forex trading, risk management, and technical analysis. Always emphasize risk management and responsible trading practices."""

@router.post("/analyze")
async def analyze_market(data: AIAnalyzeRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    FIXED: Changed from GET to POST
    Analyze market conditions for a trading pair
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Mock AI analysis (replace with actual AI integration)
    analysis = f"""
    Technical Analysis for {data.pair} ({data.timeframe}):
    
    Trend: Bullish momentum detected above 50-day MA.
    Support: Key support at recent swing low.
    Resistance: Next resistance level identified.
    Recommendation: Consider long positions on pullbacks with tight stops.
    
    Context: {data.context or 'No additional context provided'}
    """
    
    return {"analysis": analysis.strip()}

@router.post("/mentor")
async def ai_mentor(data: AIMentorRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    FIXED: Changed from GET to POST
    AI Mentor chat endpoint
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Store chat history if user is logged in
    if current_user:
        async with database.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_history (user_id, message, response, context)
                VALUES ($1, $2, $3, $4)
            """, current_user['id'], data.message, "AI response placeholder", SYSTEM_PROMPT)
    
    # Mock AI response (replace with actual AI integration)
    response = f"""
    As your trading mentor, here's my advice regarding: {data.message}
    
    1. Always use proper risk management (1-2% per trade)
    2. Verify setups with multiple timeframes
    3. Keep a trading journal to track performance
    
    Would you like me to elaborate on any of these points?
    """
    
    return {"response": response.strip()}

@router.post("/analyze-chart")
async def analyze_chart(image: str, pair: str, timeframe: str = "1H", context: Optional[str] = None):
    """Analyze uploaded chart image (placeholder)"""
    return {
        "analysis": f"Chart analysis for {pair} on {timeframe}: Pattern recognition suggests potential reversal zone. Watch for confirmation candle."
    }
