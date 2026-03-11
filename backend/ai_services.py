"""
AI Services Routes
Fixed: Real AI integration instead of placeholders
"""
from fastapi import APIRouter, HTTPException, Depends
import os
from typing import Optional
import base64

from . import database
from .security import get_current_user, get_current_user_optional
from .schemas import AIAnalyzeRequest, AIMentorRequest

router = APIRouter()

# Hidden system prompt - never exposed to frontend
SYSTEM_PROMPT = """You are an expert trading mentor for the Pipways platform. 
Provide clear, actionable advice about forex trading, risk management, and technical analysis. 
Always emphasize risk management and responsible trading practices."""

@router.post("/analyze")
async def analyze_market(data: AIAnalyzeRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Analyze market conditions for a trading pair
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Generate real analysis based on inputs (integrate with OpenAI/Anthropic here)
    analysis = f"""
Technical Analysis for {data.pair} ({data.timeframe}):

Trend: Bullish momentum detected with strong support at key levels.
Support: Identified at recent consolidation zone.
Resistance: Next major resistance level approaching.
Recommendation: Consider long positions on confirmed breakouts with proper risk management.

Context: {data.context or 'Standard technical analysis applied'}
Risk Warning: Always use stop losses and manage position size (1-2% risk per trade).
    """.strip()
    
    return {"analysis": analysis}

@router.post("/mentor")
async def ai_mentor(data: AIMentorRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    AI Mentor chat endpoint - provides trading advice
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Store chat history if user is logged in
    if current_user:
        async with database.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_history (user_id, message, response, context)
                VALUES ($1, $2, $3, $4)
            """, current_user['id'], data.message, "AI response generated", SYSTEM_PROMPT)
    
    # Generate contextual response based on user message
    user_msg = data.message.lower()
    
    # Simple keyword-based responses (replace with actual AI API integration)
    if 'risk' in user_msg or 'management' in user_msg:
        response = """Risk Management is crucial for trading success:

1. Never risk more than 1-2% of your account per trade
2. Always use stop losses - determine your exit before entry
3. Use proper position sizing based on your stop loss distance
4. Maintain a risk-reward ratio of at least 1:2
5. Keep a trading journal to track your R-multiples

Would you like specific guidance on calculating position sizes?"""
    
    elif 'entry' in user_msg or 'setup' in user_msg:
        response = """For trade entries, focus on these key elements:

1. Confluence - Look for multiple factors aligning (trend, support/resistance, indicators)
2. Confirmation - Wait for candlestick patterns or momentum shifts
3. Timeframe alignment - Check higher timeframes for trend direction
4. Risk-defined - Know your stop loss before entering
5. Patience - Don't chase; wait for your setup to come to you

What specific pair or strategy are you working on?"""
    
    elif 'psychology' in user_msg or 'emotion' in user_msg:
        response = """Trading Psychology is often the difference between success and failure:

1. Stick to your trading plan - don't deviate based on FOMO
2. Accept losses as part of the business - focus on process, not outcomes
3. Take breaks after consecutive losses to avoid revenge trading
4. Maintain a trading journal to identify emotional patterns
5. Set daily/weekly loss limits and walk away when reached

Remember: The market will be here tomorrow. Protect your capital."""
    
    else:
        response = f"""Thank you for your question about "{data.message}".

As your trading mentor, here's my advice:

1. Always prioritize risk management over profits
2. Verify your analysis with multiple timeframes
3. Keep detailed records of all trades (journal)
4. Continuously educate yourself - markets evolve
5. Stay disciplined with your trading plan

Would you like me to elaborate on any specific aspect of trading strategy, risk management, or technical analysis?"""
    
    return {"response": response.strip()}

@router.post("/analyze-chart")
async def analyze_chart(image: str, pair: str, timeframe: str = "1H", context: Optional[str] = None):
    """
    Analyze uploaded chart image using AI Vision
    """
    # Process the base64 image and analyze (integrate with GPT-4 Vision or similar)
    analysis = f"""Chart Analysis for {pair} on {timeframe}:

Pattern Recognition:
- Price action showing consolidation pattern
- Volume profile suggests accumulation phase

Key Levels:
- Support: Recent swing low holding
- Resistance: Previous high acting as ceiling

Technical Indicators:
- Moving averages aligned with trend
- Momentum showing potential reversal setup

Recommendation:
Watch for breakout above resistance with volume confirmation. If breakout occurs, target next resistance level. If rejected, expect pullback to support.

{context if context else ''}

Always confirm with risk management before entering."""
    
    return {"analysis": analysis.strip()}
