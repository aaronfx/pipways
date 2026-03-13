"""
AI Chart Analysis - PRODUCTION READY
Returns structured data for frontend visualization
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import base64
import io
from PIL import Image
import os

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .security import get_current_user

router = APIRouter()

client = None
if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/analyze")
async def analyze_chart_image(
    file: UploadFile = File(...),
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Production chart analysis with structured output for visualization
    """
    if not client:
        raise HTTPException(503, "Chart analysis service not configured. Set OPENAI_API_KEY.")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "File must be an image (PNG, JPG, JPEG)")
    
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(400, "Image too large (max 10MB)")
        
        # Process image
        image = Image.open(io.BytesIO(contents))
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # AI Vision Analysis with structured output
        response = await client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this trading chart{f' for {symbol}' if symbol else ''}{f' ({timeframe})' if timeframe else ''}.
                        
                        Identify:
                        1. Chart patterns (head & shoulders, triangles, flags, etc.)
                        2. Support and resistance levels (with approximate price values)
                        3. Trend direction
                        4. Entry, stop loss, and take profit suggestions if applicable
                        5. Confidence level (0-1)
                        
                        Return JSON format:
                        {{
                            "patterns_detected": [
                                {{"name": "pattern name", "reliability": "high|medium|low", "description": "brief description"}}
                            ],
                            "support_levels": [price1, price2],
                            "resistance_levels": [price1, price2],
                            "suggested_entry": price or null,
                            "suggested_stop": price or null,
                            "suggested_target": price or null,
                            "trading_bias": "bullish|bearish|neutral",
                            "confidence": 0.0-1.0,
                            "key_insights": ["insight1", "insight2"]
                        }}"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_str}"}
                    }
                ]
            }],
            max_tokens=1500
        )
        
        import json
        import re
        
        content = response.choices[0].message.content
        
        # Extract JSON from response
        try:
            # Try to find JSON block
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)
        except:
            # Fallback parsing
            result = {
                "patterns_detected": [],
                "support_levels": [],
                "resistance_levels": [],
                "suggested_entry": None,
                "suggested_stop": None,
                "suggested_target": None,
                "trading_bias": "neutral",
                "confidence": 0,
                "key_insights": ["Could not parse analysis"],
                "raw_response": content
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
        
        # Add image data for frontend preview
        result["image_base64"] = img_str[:100] + "..."  # Truncated for response size
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHART ERROR] {e}", flush=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.get("/pattern-library")
async def get_pattern_library():
    """Educational pattern library"""
    return {
        "reversal": [
            {"name": "Head and Shoulders", "type": "reversal", "reliability": "high", "description": "Three peaks pattern signaling trend reversal"},
            {"name": "Double Top", "type": "reversal", "reliability": "medium", "description": "Two peaks at resistance level"}
        ],
        "continuation": [
            {"name": "Bull Flag", "type": "continuation", "reliability": "medium", "description": "Sharp rise followed by consolidation"},
            {"name": "Ascending Triangle", "type": "continuation", "reliability": "medium", "description": "Flat top with rising bottom"}
        ]
    }
