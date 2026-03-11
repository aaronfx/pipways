"""
AI Services Routes
Endpoints: /api/ai/*
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from .database import db_pool
from .security import get_current_user, get_current_user_optional
from .schemas import ChatRequest
import os

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Try to import AI libraries
try:
    import openai
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
except ImportError:
    openai = None

async def call_openrouter(messages: list, model: str = "openai/gpt-4") -> str:
    """Call OpenRouter API for AI responses"""
    import httpx
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "AI service not configured. Please set OPENROUTER_API_KEY environment variable."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways Trading Platform"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return "Unable to get AI response"
    except Exception as e:
        return f"AI service error: {str(e)}"

@router.post("/chat")
async def ai_chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """AI chat endpoint with trading context"""
    system_prompt = """You are Pipways AI Trading Mentor, an expert forex trading assistant. 
    Provide concise, actionable trading advice. Focus on risk management, technical analysis, 
    and trading psychology. Keep responses under 200 words unless detailed analysis is requested."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message}
    ]

    # Add conversation history if provided
    if request.history:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in request.history[-5:]:  # Keep last 5 messages for context
            messages.append(msg)
        messages.append({"role": "user", "content": request.message})

    response = await call_openrouter(messages)

    # Save to chat history
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO chat_history (user_id, message, response, context)
            VALUES ($1, $2, $3, $4)
        """, current_user["id"], request.message, response, request.context)

    return {"response": response, "timestamp": "now"}

@router.post("/analyze-chart")
async def analyze_chart(
    image_data: str,  # base64 encoded image
    pair: str = None,
    timeframe: str = "1H",
    current_user: dict = Depends(get_current_user)
):
    """Analyze trading chart image"""
    system_prompt = """You are a professional forex chart analyst. Analyze the provided chart image 
    and identify key technical levels, patterns, trends, and potential trade setups. 
    Provide specific entry points, stop loss, and take profit levels."""

    context = f"Chart for {pair} on {timeframe} timeframe" if pair else "Trading chart"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Analyze this {context}. Identify key levels, trend direction, and potential trade setups."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_data}"}
                }
            ]
        }
    ]

    response = await call_openrouter(messages, model="anthropic/claude-3.5-sonnet")

    return {
        "analysis": response,
        "pair": pair,
        "timeframe": timeframe
    }

@router.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    """Get suggested questions for AI mentor"""
    suggestions = [
        "What's the best risk management strategy for a $1000 account?",
        "How do I identify support and resistance levels?",
        "Explain the difference between trend following and mean reversion",
        "What are the best times to trade EUR/USD?",
        "How should I handle a losing streak?",
        "Analyze the current gold market trend"
    ]
    return {"suggestions": suggestions}
