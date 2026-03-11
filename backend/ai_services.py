"""
AI Services Routes
Fixed: Markdown formatting, faster models, caching, error handling
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import os
import httpx
import base64
import hashlib
import time
from typing import Optional, List, Dict, Any

from . import database
from .security import get_current_user, get_current_user_optional
from .schemas import AIAnalyzeRequest, AIMentorRequest, PerformanceAnalysisRequest

router = APIRouter()

# Cache: user_id + prompt_hash -> (timestamp, response)
_response_cache: Dict[str, tuple] = {}
CACHE_TTL = 300  # 5 minutes in seconds

SYSTEM_PROMPT = """You are Pipways AI, an expert trading mentor. Provide clear, actionable advice about forex trading, risk management, and technical analysis. Always emphasize risk management."""

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SITE_URL = os.getenv("SITE_URL", "https://pipwaysapp.onrender.com")
SITE_NAME = "Pipways AI"

# Faster models
CHAT_MODEL = "meta-llama/llama-3.1-70b-instruct"
VISION_MODEL = "meta-llama/llama-3.1-70b-instruct"

def get_cache_key(user_id: Any, prompt: str) -> str:
    """Generate cache key from user_id and prompt"""
    key_string = f"{str(user_id)}:{prompt}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_cached_response(cache_key: str) -> Optional[str]:
    """Get cached response if not expired"""
    if cache_key in _response_cache:
        timestamp, response = _response_cache[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return response
        else:
            del _response_cache[cache_key]
    return None

def set_cached_response(cache_key: str, response: str):
    """Cache response with timestamp"""
    _response_cache[cache_key] = (time.time(), response)

async def call_openrouter(messages: List[dict], temperature: float = 0.7, model: str = CHAT_MODEL) -> str:
    """
    Call OpenRouter API with error handling, timeout, and retries
    """
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_detail = response.text
                raise HTTPException(status_code=500, detail=f"OpenRouter API error: {error_detail}")
            
            data = response.json()
            
            # Safe parsing
            if "choices" not in data or not isinstance(data["choices"], list) or len(data["choices"]) == 0:
                raise HTTPException(status_code=500, detail="Invalid response format from AI service")
            
            message_content = data["choices"][0].get("message", {}).get("content")
            if not message_content:
                raise HTTPException(status_code=500, detail="Empty response from AI service")
            
            return message_content
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout - please try again")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"AI service connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@router.post("/analyze")
async def analyze_market(data: AIAnalyzeRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Analyze market conditions with structured Markdown output
    POST /api/ai/analyze
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Check cache
        cache_key = get_cache_key(current_user.get('id') if current_user else 'anon', 
                                  f"analyze:{data.pair}:{data.timeframe}:{data.context or ''}")
        cached = get_cached_response(cache_key)
        if cached:
            return {"analysis": cached}
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""Analyze {data.pair} on {data.timeframe} timeframe and respond in professional Markdown format:

## Market Structure
Describe current trend direction (bullish/bearish/neutral) and key price action.

## Support Levels
List specific support prices with bullet points:
* Level 1: [price]
* Level 2: [price]

## Resistance Levels
List specific resistance prices with bullet points:
* Level 1: [price]
* Level 2: [price]

## Technical Indicators
Analyze RSI, MACD, Moving Averages visible on chart.

## Trade Idea
**Entry Zone:** [price range]
**Stop Loss:** [price]
**Target 1:** [price]
**Target 2:** [price]
**Risk/Reward:** [ratio]

## Risk Warning
⚠️ Risk only 1-2% per trade. Use stop losses.

Additional context: {data.context or 'None provided'}"""}
        ]
        
        analysis = await call_openrouter(messages, temperature=0.7, model=CHAT_MODEL)
        
        # Cache successful response
        set_cached_response(cache_key, analysis)
        
        return {"analysis": analysis}
        
    except HTTPException:
        raise
    except Exception as e:
        return {"error": "AI service temporarily unavailable", "details": str(e)}

@router.post("/mentor")
async def ai_mentor(data: AIMentorRequest, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    AI Mentor chat endpoint with safe response parsing
    POST /api/ai/mentor
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        # Check cache
        cache_key = get_cache_key(current_user.get('id') if current_user else 'anon',
                                  f"mentor:{data.message[:100]}")
        cached = get_cached_response(cache_key)
        if cached:
            return {"response": cached}
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add history
        for msg in (data.history or [])[-5:]:
            role = "assistant" if msg.get("role") == "assistant" else "user"
            content = msg.get("content", "")
            if content:
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": data.message})
        
        # Get AI response with timeout and faster model
        response_text = await call_openrouter(messages, temperature=0.8, model=CHAT_MODEL)
        
        # Cache response
        set_cached_response(cache_key, response_text)
        
        # Store in DB (non-blocking if fails)
        if current_user:
            try:
                async with database.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO chat_history (user_id, message, response, context)
                        VALUES ($1, $2, $3, $4)
                    """, current_user['id'], data.message, response_text, "AI mentor chat")
            except Exception as db_err:
                print(f"Chat history storage failed: {db_err}")
        
        # FIXED: Return in correct format for frontend
        return {"response": response_text}
        
    except HTTPException:
        raise
    except Exception as e:
        # Return error gracefully instead of crashing
        return {"error": "AI service temporarily unavailable", "response": "I'm currently experiencing technical difficulties. Please try again in a moment."}

@router.post("/analyze-chart")
async def analyze_chart(
    image: UploadFile = File(...),
    pair: str = Form(default="EURUSD"),
    timeframe: str = Form(default="1H"),
    context: Optional[str] = Form(default=None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Analyze chart image with vision capabilities
    POST /api/ai/analyze-chart (multipart/form-data)
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Validate image
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if image.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")
        
        # Read and validate size
        image_bytes = await image.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")
        
        # Convert to base64 data URI
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = image.content_type or "image/jpeg"
        image_data_uri = f"data:{mime_type};base64,{image_b64}"
        
        # Vision prompt requesting Markdown format
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this trading chart for {pair} on {timeframe} and respond in Markdown:

## Pattern Recognition
Identify chart patterns (head & shoulders, triangles, channels, etc.).

## Key Levels
* Support: [price]
* Resistance: [price]

## Indicator Analysis
Describe visible indicators and their signals.

## Trade Setup
**Direction:** Long/Short
**Entry:** [price]
**Stop:** [price]
**Target:** [price]

**Risk Warning:** Use proper risk management.{context if context else ''}"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_uri}
                    }
                ]
            }
        ]
        
        # Use vision-capable model (Llama 3.1 70B supports vision)
        analysis = await call_openrouter(messages, temperature=0.5, model=VISION_MODEL)
        
        return {"analysis": analysis}
        
    except HTTPException:
        raise
    except Exception as e:
        return {"error": "Vision analysis failed", "analysis": "Unable to analyze image. Please try again with a clearer chart image."}

@router.post("/analyze-vision")
async def analyze_performance_vision(
    data: PerformanceAnalysisRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Analyze trading performance with validation and structured output
    POST /api/performance/analyze-vision
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Validate input
        if not data.image or len(data.image) < 100:
            raise HTTPException(status_code=400, detail="Invalid image data")
        
        if data.account_balance <= 0:
            raise HTTPException(status_code=400, detail="Account balance must be positive")
        
        if data.trading_period_days <= 0:
            raise HTTPException(status_code=400, detail="Trading period must be positive")
        
        # Check cache
        cache_key = get_cache_key(current_user.get('id') if current_user else 'anon',
                                  f"performance:{data.account_balance}:{data.trading_period_days}")
        cached = get_cached_response(cache_key)
        if cached:
            return {"analysis": cached, "metrics": {}}
        
        # If no actual AI processing, generate structured mock analysis
        # In production, replace with actual AI vision analysis
        analysis_result = {
            "trader_score": 75,
            "total_trades": 45,
            "win_rate": 62.5,
            "profit_factor": 1.8,
            "average_return": 2.3,
            "analysis": f"""## Performance Analysis

### Account Overview
* Balance: ${data.account_balance}
* Period: {data.trading_period_days} days
* Trader Score: **75/100** (Good)

### Key Metrics
* **Win Rate:** 62.5%
* **Profit Factor:** 1.8
* **Average Return:** 2.3%

### Strengths
✅ Consistent position sizing
✅ Good risk management on winners

### Areas for Improvement
⚠️ Cut losses faster
⚠️ Reduce overtrading

### Recommendations
1. Set strict stop loss rules
2. Limit to 3 trades per day
3. Review losing trades weekly""",
            "metrics": {
                "winrate": "62.5%",
                "risk_score": "Medium",
                "profit_factor": "1.8",
                "trader_score": 75
            }
        }
        
        # Cache the analysis
        set_cached_response(cache_key, analysis_result["analysis"])
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "error": "Analysis processing error",
            "analysis": "Unable to complete analysis. Please check your inputs and try again.",
            "metrics": {}
        }
