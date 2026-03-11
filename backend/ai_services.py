"""
AI Services Routes
Fixed: Real OpenRouter API integration
"""
from fastapi import APIRouter, HTTPException, Depends
import os
import httpx
from typing import Optional, List
import json

from . import database
from .security import get_current_user, get_current_user_optional
from .schemas import AIAnalyzeRequest, AIMentorRequest

router = APIRouter()

# Hidden system prompt - never exposed to frontend
SYSTEM_PROMPT = """You are Pipways AI, an expert trading mentor. Provide clear, actionable advice about forex trading, risk management, and technical analysis. Always emphasize risk management and responsible trading practices. Be concise but thorough."""

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SITE_URL = "https://pipwaysapp.onrender.com"
SITE_NAME = "Pipways AI"

async def call_openrouter(messages: List[dict], temperature: float = 0.7):
    """Call OpenRouter API with proper headers"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": SITE_URL,
        "X-Title": SITE_NAME,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openrouter/auto",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            error_text = response.text
            raise HTTPException(status_code=500, detail=f"AI service error: {error_text}")
        
        data = response.json()
        return data["choices"][0]["message"]["content"]

@router.post("/analyze")
async def analyze_market(data: AIAnalyzeRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Analyze market conditions for a trading pair using OpenRouter
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Provide technical analysis for {data.pair} on {data.timeframe} timeframe.
            
Additional context: {data.context or 'None provided'}

Include:
1. Trend direction and strength
2. Key support and resistance levels
3. Entry and exit recommendations
4. Risk management advice
5. Key technical indicators to watch"""}
        ]
        
        analysis = await call_openrouter(messages)
        return {"analysis": analysis}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mentor")
async def ai_mentor(data: AIMentorRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    AI Mentor chat endpoint using OpenRouter
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Build conversation history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add recent history
        for msg in data.history[-5:]:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
        
        # Add current message
        messages.append({"role": "user", "content": data.message})
        
        response_text = await call_openrouter(messages)
        
        # Store chat history if user is logged in
        if current_user:
            async with database.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO chat_history (user_id, message, response, context)
                    VALUES ($1, $2, $3, $4)
                """, current_user['id'], data.message, response_text, "AI mentor chat")
        
        return {"response": response_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-chart")
async def analyze_chart(data: dict, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Analyze uploaded chart image using OpenRouter Vision
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        image_data = data.get("image", "")
        pair = data.get("pair", "EURUSD")
        timeframe = data.get("timeframe", "1H")
        context = data.get("context", "")
        
        # Prepare vision-capable message
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this trading chart for {pair} on {timeframe} timeframe. 
                        
Context: {context if context else 'No additional context'}

Provide:
1. Pattern recognition (support/resistance, trendlines, chart patterns)
2. Technical indicator signals visible
3. Entry/exit recommendations
4. Risk management levels (SL/TP suggestions)"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data if image_data.startswith("http") else f"data:image/jpeg;base64,{image_data.split(',')[1] if ',' in image_data else image_data}"
                        }
                    }
                ]
            }
        ]
        
        analysis = await call_openrouter(messages, temperature=0.5)
        return {"analysis": analysis}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
