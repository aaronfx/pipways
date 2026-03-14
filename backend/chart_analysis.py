"""
AI Chart Analysis - PRODUCTION READY
Uses OpenRouter Vision API (Claude 3.5 Sonnet via OpenRouter)
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
import base64
import io
import os
import httpx
import json
import re

from PIL import Image
from .security import get_current_user

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_VISION_MODEL") or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Common symbols for detection
COMMON_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "XAGUSD", 
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "US30", "US100", "DE30"
]

def extract_symbol_from_text(text: str) -> Optional[str]:
    """Extract trading symbol from AI response"""
    if not text:
        return None
    text_upper = text.upper()
    for symbol in COMMON_SYMBOLS:
        if symbol in text_upper:
            return symbol

    # Forex pattern
    match = re.search(r'([A-Z]{3})([A-Z]{3})', text_upper)
    if match:
        return match.group(0)
    return None

@router.post("/analyze")
async def analyze_chart_image(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """
    Chart Analysis using OpenRouter Vision API.
    Returns structured analysis with trade setup.
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "File must be an image (PNG, JPG, JPEG, WEBP)")

    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(400, "Image too large (max 10MB)")

        if len(contents) == 0:
            raise HTTPException(400, "Empty file uploaded")

        # Store image for response
        base64_image = base64.b64encode(contents).decode('utf-8')
        content_type = file.content_type or "image/jpeg"

        if not OPENROUTER_CONFIGURED:
            demo_symbol = symbol or "EURUSD"
            return {
                "symbol": demo_symbol,
                "trading_bias": "neutral",
                "confidence": 0.75,
                "patterns_detected": [
                    {"name": "Support Test", "reliability": "medium"},
                    {"name": "Consolidation", "reliability": "high"}
                ],
                "support_levels": ["1.0850", "1.0820"],
                "resistance_levels": ["1.0950", "1.1000"],
                "suggested_entry": "1.0860",
                "suggested_stop": "1.0830",
                "suggested_target": "1.0940",
                "key_insights": [
                    f"{demo_symbol} showing consolidation at support",
                    "Configure OPENROUTER_API_KEY for AI-powered analysis"
                ],
                "chart_image": f"data:{content_type};base64,{base64_image}",
                "trade_setup": {
                    "entry": "1.0860",
                    "stop_loss": "1.0830",
                    "take_profit": "1.0940",
                    "risk_reward": "1:2.7",
                    "probability": 0.75,
                    "direction": "BUY"
                },
                "mode": "demo",
                "configured": False
            }

        # Process image
        try:
            image = Image.open(io.BytesIO(contents))
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            data_url = f"data:image/png;base64,{img_str}"
        except Exception:
            data_url = f"data:{content_type};base64,{base64_image}"

        symbol_context = f"Symbol: {symbol}" if symbol else "Symbol: Unknown - detect from chart"
        timeframe_context = f"Timeframe: {timeframe}" if timeframe else "Timeframe: Unknown"

        system_prompt = """You are a professional trading chart analyst. Analyze the provided chart image and identify:
1. The trading symbol/pair if visible on the chart
2. Chart patterns (head & shoulders, triangles, flags, wedges, double tops/bottoms, etc.)
3. Support and resistance levels (with approximate price values)
4. Trend direction (bullish, bearish, or neutral)
5. Specific trade suggestions: entry price, stop loss, and take profit levels if a setup is present
6. Confidence level (0.0 to 1.0) in your analysis

Return your analysis in strict JSON format:
{
    "symbol": "detected symbol or Unknown",
    "patterns_detected": [
        {"name": "pattern name", "reliability": "high|medium|low", "description": "brief description"}
    ],
    "support_levels": ["price1", "price2"],
    "resistance_levels": ["price1", "price2"],
    "suggested_entry": "price or null",
    "suggested_stop": "price or null",
    "suggested_target": "price or null",
    "trading_bias": "bullish|bearish|neutral",
    "confidence": 0.0-1.0,
    "key_insights": ["insight1", "insight2"],
    "risk_reward_ratio": "1:2.5",
    "structure_quality": "strong|weak|neutral"
}

Be precise with price levels. Use null for fields not applicable. Return ONLY the JSON object."""

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
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Analyze this trading chart. {symbol_context}. {timeframe_context}. Detect the symbol if visible, identify patterns, key levels, and suggest trade setup. Return JSON only."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_url, "detail": "high"}
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.2
                },
                timeout=60.0
            )

            if response.status_code != 200:
                error_text = response.text
                print(f"[CHART ANALYSIS ERROR] HTTP {response.status_code}: {error_text}", flush=True)
                if response.status_code == 401:
                    raise HTTPException(503, "AI authentication failed. Check API key.")
                elif response.status_code == 429:
                    raise HTTPException(503, "AI service rate limited. Please try again.")
                else:
                    raise HTTPException(503, f"AI service error: {response.status_code}")

            data = response.json()

            if "choices" not in data or len(data["choices"]) == 0:
                raise HTTPException(503, "Invalid response from AI service")

            content = data["choices"][0]["message"]["content"]

            # Parse JSON
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(content)
            except json.JSONDecodeError:
                print(f"[CHART ANALYSIS] JSON parse failed, content: {content[:200]}", flush=True)
                detected_symbol = extract_symbol_from_text(content) or symbol or "Unknown"
                result = {
                    "symbol": detected_symbol,
                    "patterns_detected": [],
                    "support_levels": [],
                    "resistance_levels": [],
                    "suggested_entry": None,
                    "suggested_stop": None,
                    "suggested_target": None,
                    "trading_bias": "neutral",
                    "confidence": 0,
                    "key_insights": [content[:300]],
                    "structure_quality": "neutral"
                }

            # Ensure symbol
            if not result.get("symbol") or result["symbol"] == "Unknown":
                result["symbol"] = extract_symbol_from_text(content) or symbol or "Unknown"

            # Add chart image to result
            result["chart_image"] = f"data:{content_type};base64,{base64_image}"

            # Build trade setup
            if result.get("suggested_entry") and result.get("suggested_stop") and result.get("suggested_target"):
                try:
                    entry = float(str(result["suggested_entry"]).replace(",", ""))
                    sl = float(str(result["suggested_stop"]).replace(",", ""))
                    tp = float(str(result["suggested_target"]).replace(",", ""))

                    risk = abs(entry - sl)
                    reward = abs(tp - entry)
                    rr = f"1:{reward/risk:.1f}" if risk > 0 else "N/A"

                    result["trade_setup"] = {
                        "entry": str(entry),
                        "stop_loss": str(sl),
                        "take_profit": str(tp),
                        "risk_reward": rr,
                        "probability": result.get("confidence", 0.7),
                        "direction": result.get("trading_bias", "neutral").upper(),
                        "quality": result.get("structure_quality", "neutral")
                    }
                except:
                    result["trade_setup"] = None

            result["mode"] = "ai"
            result["configured"] = True

            return result

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "Chart analysis timed out. Try a smaller image.")
    except Exception as e:
        print(f"[CHART ANALYSIS ERROR] {e}", flush=True)
        raise HTTPException(503, f"Analysis service unavailable: {str(e)}")

@router.get("/pattern-library")
async def get_pattern_library():
    """Educational pattern library - static data"""
    return {
        "reversal": [
            {"name": "Head and Shoulders", "type": "reversal", "reliability": "high", "description": "Three peaks pattern signaling trend reversal", "success_rate": "65%"},
            {"name": "Double Top", "type": "reversal", "reliability": "medium", "description": "Two peaks at resistance level", "success_rate": "60%"},
            {"name": "Double Bottom", "type": "reversal", "reliability": "medium", "description": "Two lows at support level", "success_rate": "60%"}
        ],
        "continuation": [
            {"name": "Bull Flag", "type": "continuation", "reliability": "medium", "description": "Sharp rise followed by consolidation", "success_rate": "67%"},
            {"name": "Bear Flag", "type": "continuation", "reliability": "medium", "description": "Sharp drop followed by consolidation", "success_rate": "67%"},
            {"name": "Ascending Triangle", "type": "continuation", "reliability": "medium", "description": "Flat top with rising bottom", "success_rate": "62%"}
        ],
        "candlestick": [
            {"name": "Doji", "type": "candlestick", "reliability": "medium", "description": "Indecision in the market", "success_rate": "55%"},
            {"name": "Engulfing Pattern", "type": "candlestick", "reliability": "high", "description": "Strong reversal signal", "success_rate": "72%"},
            {"name": "Hammer", "type": "candlestick", "reliability": "medium", "description": "Potential bottom reversal", "success_rate": "60%"}
        ]
    }
