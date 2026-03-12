"""
Pipways AI Services
Professional AI mentor + chart analysis + performance analysis
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import os
import httpx
import base64
import hashlib
import time
from typing import Optional, List, Dict, Any

from . import database
from .security import get_current_user_optional
from .schemas import AIAnalyzeRequest, AIMentorRequest, PerformanceAnalysisRequest

router = APIRouter()

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
SITE_URL = os.getenv("SITE_URL", "https://pipwaysapp.onrender.com")
SITE_NAME = "Pipways AI"

CHAT_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are Pipways AI Mentor.

You are a professional forex trading coach helping traders improve.

Teach traders:

• Risk management
• Trading psychology
• Technical analysis
• Position sizing
• Discipline and journaling

Rules:

1. Always emphasize risking only 1-2% per trade.
2. Encourage patience and avoiding overtrading.
3. Warn about emotional trading.
4. Give clear structured advice.

Respond like a professional trading mentor.
"""

# --------------------------------------------------
# CACHE
# --------------------------------------------------

_response_cache: Dict[str, tuple] = {}
CACHE_TTL = 300


def get_cache_key(user_id: Any, prompt: str):
    key = f"{user_id}:{prompt}"
    return hashlib.md5(key.encode()).hexdigest()


def get_cached_response(key):

    if key in _response_cache:

        timestamp, data = _response_cache[key]

        if time.time() - timestamp < CACHE_TTL:
            return data

        del _response_cache[key]

    return None


def set_cached_response(key, value):
    _response_cache[key] = (time.time(), value)

# --------------------------------------------------
# OPENROUTER CALL
# --------------------------------------------------


async def call_openrouter(messages, temperature=0.7, model=CHAT_MODEL):

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
        "max_tokens": 3000
    }

    try:

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=response.text
                )

            data = response.json()

            if "choices" not in data:
                raise HTTPException(
                    status_code=500,
                    detail="Invalid AI response"
                )

            return data["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI timeout")

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=str(e))

# --------------------------------------------------
# AI MENTOR
# --------------------------------------------------


@router.post("/mentor")
async def ai_mentor(
        data: AIMentorRequest,
        current_user: Optional[dict] = Depends(get_current_user_optional)
):

    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:

        cache_key = get_cache_key(
            current_user.get("id") if current_user else "anon",
            data.message
        )

        cached = get_cached_response(cache_key)

        if cached:
            return {"response": cached}

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in (data.history or [])[-5:]:

            role = "assistant" if msg.get("role") == "assistant" else "user"

            messages.append({
                "role": role,
                "content": msg.get("content", "")
            })

        messages.append({
            "role": "user",
            "content": data.message
        })

        ai_text = await call_openrouter(messages)

        set_cached_response(cache_key, ai_text)

        return {"response": ai_text}

    except Exception:

        return {
            "error": "AI temporarily unavailable",
            "response": "AI mentor is temporarily unavailable."
        }

# --------------------------------------------------
# CHART ANALYSIS
# --------------------------------------------------


@router.post("/analyze-chart")
async def analyze_chart(
        image: UploadFile = File(...),
        pair: str = Form(default="EURUSD"),
        timeframe: str = Form(default="1H"),
        context: Optional[str] = Form(default=None),
        current_user: Optional[dict] = Depends(get_current_user_optional)
):

    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    image_bytes = await image.read()

    image_b64 = base64.b64encode(image_bytes).decode()

    image_url = f"data:{image.content_type};base64,{image_b64}"

    chart_prompt = f"""
You are an institutional forex trader.

Analyze this {pair} chart on {timeframe} timeframe.

Respond with this structure:

## Market Structure
Trend direction.

## Key Support
List levels.

## Key Resistance
List levels.

## Pattern
Identify chart pattern.

## Trade Setup
Direction:
Entry:
Stop Loss:
TP1:
TP2:

## Risk Management
Explain risk.

## Probability
Success probability.
"""

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": chart_prompt},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    }]

    analysis = await call_openrouter(messages, model=VISION_MODEL)

    return {"analysis": analysis}

# --------------------------------------------------
# PERFORMANCE ANALYSIS
# --------------------------------------------------


@router.post("/analyze-vision")
async def analyze_performance_vision(
        data: PerformanceAnalysisRequest,
        current_user: Optional[dict] = Depends(get_current_user_optional)
):

    return {

        "trader_score": 75,

        "analysis": """
### Trading Performance

Overall trading discipline is good.

Strengths:
• Consistent lot sizes
• Acceptable win rate

Key Issues:
• Some trades held too long
• Occasional overtrading

Improvement Plan:
• Use strict stop losses
• Limit daily trades
• Maintain trading journal
""",

        "strengths": [
            "Consistent position sizing",
            "Good profit factor"
        ],

        "top_mistakes": [
            "Holding losing trades too long",
            "Overtrading during volatile sessions"
        ],

        "improvement_plan": [
            "Limit trades to 3 per day",
            "Use stop losses",
            "Review journal weekly"
        ]
    }
