"""
Pipways AI Services
Handles:
- AI Mentor
- Chart Analysis
- Performance Analysis
"""

import os
import httpx
import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

from . import database
from .security import get_current_user_optional
from .schemas import AIMentorRequest, PerformanceAnalysisRequest

router = APIRouter()

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SITE_URL = os.getenv("SITE_URL", "https://pipwaysapp.onrender.com")
SITE_NAME = "Pipways AI"

CHAT_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are Pipways AI Mentor.

You are a professional forex trading coach helping traders improve.

Teach traders:
- risk management
- trading psychology
- technical analysis
- discipline

Always emphasize risking only 1-2% per trade.
"""

# --------------------------------------------------
# OPENROUTER CALL
# --------------------------------------------------

async def call_openrouter(messages, model=CHAT_MODEL):

    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": SITE_URL,
        "X-Title": SITE_NAME,
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 3000
    }

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

        return data["choices"][0]["message"]["content"]

# --------------------------------------------------
# AI MENTOR
# --------------------------------------------------

@router.post("/mentor")
async def ai_mentor(
    data: AIMentorRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": data.message}
    ]

    response = await call_openrouter(messages)

    return {"response": response}

# --------------------------------------------------
# CHART ANALYSIS
# --------------------------------------------------

@router.post("/analyze-chart")
async def analyze_chart(
    image: UploadFile = File(...),
    pair: str = Form("EURUSD"),
    timeframe: str = Form("1H"),
    context: str = Form("")
):

    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode()

    chart_prompt = f"""
Analyze this {pair} chart on {timeframe} timeframe.

Return structured analysis:

Market Structure
Support
Resistance
Trade Setup
Entry
Stop Loss
Take Profit
Probability
"""

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": chart_prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.content_type};base64,{image_b64}"
                }
            }
        ]
    }]

    analysis = await call_openrouter(messages, model=VISION_MODEL)

    return {"analysis": analysis}

# --------------------------------------------------
# PERFORMANCE ANALYSIS
# --------------------------------------------------

@router.post("/analyze-performance")
async def analyze_performance(
    data: PerformanceAnalysisRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):

    # Placeholder until CSV parser added

    return {

        "trader_score": 75,

        "analysis": """
### Performance Summary

You show decent trading discipline.

### Key Issues
Holding losing trades too long
Overtrading during volatile sessions

### Strengths
Consistent position sizing
Good profit factor

### Improvement Plan
Limit trades to 3 per day
Use stop losses
Review journal weekly
""",

        "strengths": [
            "Consistent position sizing",
            "Good profit factor"
        ],

        "top_mistakes": [
            "Holding losing trades too long",
            "Overtrading volatile sessions"
        ],

        "improvement_plan": [
            "Limit trades to 3 per day",
            "Use hard stop losses",
            "Maintain trading journal"
        ]
    }
