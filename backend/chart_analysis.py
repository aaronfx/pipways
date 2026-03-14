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

@router.post("/analyze")
async def analyze_chart_image(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """
    Chart Analysis using OpenRouter Vision API.
    Returns 503 if OpenRouter is not configured.
    """
    if not OPENROUTER_CONFIGURED:
        raise HTTPException(
            status_code=503, 
            detail="Chart analysis service not configured. Set OPENROUTER_API_KEY."
        )
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "File must be an image (PNG, JPG, JPEG, WEBP)")
    
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(400, "Image too large (max 10MB)")
        
        if len(contents) == 0:
            raise HTTPException(400, "Empty file uploaded")
        
        # Process image - convert to PNG for consistency
        try:
            image = Image.open(io.BytesIO(contents))
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            data_url = f"data:image/png;base64,{img_str}"
        except Exception:
            # If PIL fails, try raw base64 of original
            data_url = f"data:{file.content_type};base64,{base64.b64encode(contents).decode('utf-8')}"
        
        symbol_context = f"Symbol: {symbol}" if symbol else "Symbol: Unknown"
        timeframe_context = f"Timeframe: {timeframe}" if timeframe else "Timeframe: Unknown"
        
        system_prompt = """You are a professional trading chart analyst. Analyze the provided chart image and identify:
1. Chart patterns (head & shoulders, triangles, flags, wedges, double tops/bottoms, etc.)
2. Support and resistance levels (with approximate price values)
3. Trend direction (bullish, bearish, or neutral)
4. Specific trade suggestions: entry price, stop loss, and take profit levels if a setup is present
5. Confidence level (0.0 to 1.0) in your analysis

Return your analysis in strict JSON format with this structure:
{
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
    "key_insights": ["insight1", "insight2"]
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
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Analyze this trading chart. {symbol_context}. {timeframe_context}. Provide detailed technical analysis and return JSON only."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": data_url,
                                        "detail": "high"
                                    }
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
                print(f"[CHART ANALYSIS ERROR] OpenRouter HTTP {response.status_code}: {error_text}", flush=True)
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
            
            # Parse JSON from response
            try:
                # Try to extract JSON from markdown code blocks if present
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(content)
            except json.JSONDecodeError:
                print(f"[CHART ANALYSIS] JSON parse failed, content: {content[:200]}", flush=True)
                # Fallback structure
                result = {
                    "patterns_detected": [],
                    "support_levels": [],
                    "resistance_levels": [],
                    "suggested_entry": None,
                    "suggested_stop": None,
                    "suggested_target": None,
                    "trading_bias": "neutral",
                    "confidence": 0,
                    "key_insights": ["Could not parse structured analysis", content[:100]],
                    "parse_error": True
                }
            
            # Ensure all required fields exist
            result.setdefault("patterns_detected", [])
            result.setdefault("support_levels", [])
            result.setdefault("resistance_levels", [])
            result.setdefault("suggested_entry", None)
            result.setdefault("suggested_stop", None)
            result.setdefault("suggested_target", None)
            result.setdefault("trading_bias", "neutral")
            result.setdefault("confidence", 0)
            result.setdefault("key_insights", [])
            
            return result
            
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "Chart analysis timed out. Try a smaller image or try again.")
    except Exception as e:
        print(f"[CHART ANALYSIS ERROR] {e}", flush=True)
        raise HTTPException(503, f"Analysis service unavailable: {str(e)}")

@router.get("/pattern-library")
async def get_pattern_library():
    """Educational pattern library - static data"""
    return {
        "reversal": [
            {"name": "Head and Shoulders", "type": "reversal", "reliability": "high", "description": "Three peaks pattern signaling trend reversal", "success_rate": "65%"},
            {"name": "Double Top", "type": "reversal", "reliability": "medium", "description": "Two peaks at resistance level", "success_rate": "60%"}
        ],
        "continuation": [
            {"name": "Bull Flag", "type": "continuation", "reliability": "medium", "description": "Sharp rise followed by consolidation", "success_rate": "67%"},
            {"name": "Ascending Triangle", "type": "continuation", "reliability": "medium", "description": "Flat top with rising bottom", "success_rate": "62%"}
        ],
        "candlestick": [
            {"name": "Doji", "type": "candlestick", "reliability": "medium", "description": "Indecision in the market", "success_rate": "55%"},
            {"name": "Engulfing Pattern", "type": "candlestick", "reliability": "high", "description": "Strong reversal signal", "success_rate": "72%"}
        ]
    }
