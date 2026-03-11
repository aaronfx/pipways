"""
AI Services Routes
Fixed: Proper OpenRouter integration with FormData support for Vision
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import os
import httpx
import base64
from typing import Optional, List

from . import database
from .security import get_current_user, get_current_user_optional
from .schemas import AIAnalyzeRequest, AIMentorRequest

router = APIRouter()

SYSTEM_PROMPT = """You are Pipways AI, an expert trading mentor. Provide clear, actionable advice about forex trading, risk management, and technical analysis. Always emphasize risk management and responsible trading practices."""

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SITE_URL = os.getenv("SITE_URL", "https://pipwaysapp.onrender.com")
SITE_NAME = "Pipways AI"

async def call_openrouter(messages: List[dict], temperature: float = 0.7, model: str = "openrouter/auto"):
    """Call OpenRouter API with proper headers"""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured - missing OPENROUTER_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": SITE_URL,
        "X-Title": SITE_NAME,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2000
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_text = response.text
                raise HTTPException(status_code=500, detail=f"OpenRouter error: {error_text}")
            
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                raise HTTPException(status_code=500, detail="Invalid response from AI service")
            
            return data["choices"][0]["message"]["content"]
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@router.post("/analyze")
async def analyze_market(data: AIAnalyzeRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Analyze market conditions for a trading pair
    POST /api/ai/analyze
    Body: {"pair": "EURUSD", "timeframe": "1H", "context": "optional context"}
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
5. Key technical indicators to watch

Be concise and actionable."""}
        ]
        
        analysis = await call_openrouter(messages, temperature=0.7, model="openrouter/auto")
        return {"analysis": analysis}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mentor")
async def ai_mentor(data: AIMentorRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    AI Mentor chat endpoint
    POST /api/ai/mentor
    Body: {"message": "user message", "history": [], "use_knowledge": true}
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add recent history (last 10 messages)
        for msg in (data.history or [])[-10:]:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "")
            if content:
                messages.append({"role": role, "content": content})
        
        # Add current message
        messages.append({"role": "user", "content": data.message})
        
        response_text = await call_openrouter(messages, temperature=0.8, model="openrouter/auto")
        
        # Store chat history if user is logged in
        if current_user:
            try:
                async with database.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO chat_history (user_id, message, response, context)
                        VALUES ($1, $2, $3, $4)
                    """, current_user['id'], data.message, response_text, "AI mentor chat")
            except Exception as db_error:
                # Log but don't fail if DB storage fails
                print(f"Failed to store chat history: {db_error}")
        
        return {"response": response_text}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-chart")
async def analyze_chart(
    image: UploadFile = File(..., description="Chart image file"),
    pair: str = Form(default="EURUSD", description="Trading pair"),
    timeframe: str = Form(default="1H", description="Timeframe"),
    context: Optional[str] = Form(default=None, description="Additional context"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Analyze uploaded chart image using AI Vision
    POST /api/ai/analyze-chart
    Content-Type: multipart/form-data
    Fields: image (file), pair (string), timeframe (string), context (string, optional)
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Validate image type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")
        
        # Read file and convert to base64
        image_bytes = await image.read()
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = image.content_type or "image/jpeg"
        image_data_uri = f"data:{mime_type};base64,{image_base64}"
        
        # Prepare vision message for OpenRouter
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this trading chart for {pair} on {timeframe} timeframe.
                        
{f'Context: {context}' if context else ''}

Provide specific analysis:
1. Pattern recognition (support/resistance levels, trendlines, chart patterns)
2. Technical indicators visible (moving averages, oscillators, etc.)
3. Entry/exit recommendations with specific price levels
4. Risk management suggestions (stop loss placement)
5. Trade setup rating (High/Medium/Low probability)

Be specific and actionable."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_uri
                        }
                    }
                ]
            }
        ]
        
        # Use GPT-4o for vision (reliable vision model)
        analysis = await call_openrouter(
            messages, 
            temperature=0.5, 
            model="openai/gpt-4o"
        )
        
        return {"analysis": analysis}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")
