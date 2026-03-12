"""
Pipways AI Services
"""

import os
import httpx
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from .services.performance_parser import parse_statement
from .services.trading_metrics import calculate_metrics

router = APIRouter()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are Pipways AI Trading Mentor.

Provide professional trading insights about:

• risk management
• trading psychology
• discipline
• technical analysis

Always emphasize risking only 1–2% per trade.
"""


async def call_openrouter(messages, model):

    if not OPENROUTER_API_KEY:
        raise HTTPException(500, "OpenRouter API key not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2000
    }

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise HTTPException(500, response.text)

        data = response.json()

        return data["choices"][0]["message"]["content"]


# ------------------------------
# AI MENTOR (UNCHANGED)
# ------------------------------

@router.post("/mentor")
async def ai_mentor(data: dict):

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": data.get("message")}
    ]

    response = await call_openrouter(messages, OPENROUTER_MODEL)

    return {"response": response}


# ------------------------------
# CHART ANALYZER (UNCHANGED)
# ------------------------------

@router.post("/analyze-chart")
async def analyze_chart(
    image: UploadFile = File(...),
    pair: str = Form("EURUSD"),
    timeframe: str = Form("1H"),
    context: str = Form("")
):

    image_bytes = await image.read()

    image_b64 = base64.b64encode(image_bytes).decode()

    prompt = f"""
Analyze this {pair} chart on the {timeframe} timeframe.

Return:

Market Bias
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
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.content_type};base64,{image_b64}"
                }
            }
        ]
    }]

    analysis = await call_openrouter(messages, OPENROUTER_VISION_MODEL)

    return {"analysis": analysis}


# ------------------------------
# NEW ADVANCED PERFORMANCE ANALYZER
# ------------------------------

@router.post("/analyze-performance-file")
async def analyze_performance_file(file: UploadFile = File(...)):

    file_bytes = await file.read()

    df = parse_statement(file_bytes, file.filename)

    metrics = calculate_metrics(df)

    metrics_text = f"""
Trades: {metrics['trades']}
Win Rate: {metrics['win_rate']}%
Profit Factor: {metrics['profit_factor']}
Risk Reward: {metrics['risk_reward']}
Expectancy: {metrics['expectancy']}
"""

    prompt = f"""
You are a hedge fund trading performance coach.

Analyze the following trading statistics.

{metrics_text}

Return insights in these sections:

Performance Summary
Key Issues
Strengths
Improvement Plan
Recommended Courses
Mentor Advice
Risk Management Score
Discipline Score
"""

    ai_analysis = await call_openrouter(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        OPENROUTER_MODEL
    )

    return {
        "metrics": metrics,
        "analysis": ai_analysis
    }
