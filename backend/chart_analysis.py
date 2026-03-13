"""
AI Chart Analysis - Pattern Recognition from Images
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Literal
import base64
import io
from PIL import Image
import os
import json
import re
from openai import AsyncOpenAI

from .security import get_current_user

router = APIRouter(prefix="", tags=["chart-analysis"])

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

class PatternRecognitionResult(BaseModel):
    patterns_detected: List[dict]
    trend_direction: str
    support_levels: List[float]
    resistance_levels: List[float]
    key_insights: List[str]
    trading_bias: Literal["bullish", "bearish", "neutral"]
    confidence: float

@router.post("/analyze")
async def analyze_chart_image(
    file: UploadFile = File(...),
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Upload a chart image for AI pattern recognition.
    Detects: Head & Shoulders, Triangles, Flags, Double Tops/Bottoms, etc.
    """
    if not os.getenv("OPENAI_API_KEY"):
        # Return demo analysis when OpenAI is not configured
        return {
            "patterns_detected": [
                {"name": "Bull Flag", "reliability": "medium", "description": "Continuation pattern detected"},
                {"name": "Support Bounce", "reliability": "high", "description": "Price bouncing off key support"}
            ],
            "trend_direction": "bullish",
            "support_levels": [1.0820, 1.0800],
            "resistance_levels": [1.0900, 1.0950],
            "key_insights": [
                "Strong support at 1.0820 level",
                "Bullish momentum building",
                "Consider long positions above 1.0850"
            ],
            "trading_bias": "bullish",
            "confidence": 0.75
        }
    
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "File must be an image")
    
    try:
        # Read and resize image
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(400, "Image too large (max 5MB)")
        
        image = Image.open(io.BytesIO(contents))
        
        # Convert to base64 for OpenAI Vision
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # AI Vision Analysis
        response = await client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this trading chart{f' for {symbol}' if symbol else ''}{f' on {timeframe}' if timeframe else ''}. 
                            Identify:
                            1. Chart patterns (head & shoulders, triangles, flags, double tops/bottoms, wedges)
                            2. Trend direction and strength
                            3. Key support and resistance levels
                            4. Candlestick patterns
                            5. Entry/exit suggestions
                            
                            Return JSON format with patterns_detected (array with name, reliability, description), 
                            trend_direction, support_levels, resistance_levels, key_insights (array), 
                            trading_bias (bullish/bearish/neutral), and confidence (0-1)."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        analysis_text = response.choices[0].message.content
        
        # Parse JSON from response (may need cleaning)
        try:
            result = json.loads(analysis_text)
        except:
            # Extract JSON from markdown if wrapped
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    "patterns_detected": [],
                    "trend_direction": "unknown",
                    "support_levels": [],
                    "resistance_levels": [],
                    "key_insights": ["Unable to parse chart automatically"],
                    "trading_bias": "neutral",
                    "confidence": 0.0,
                    "raw_response": analysis_text
                }
        
        return PatternRecognitionResult(**result)
        
    except Exception as e:
        raise HTTPException(500, f"Chart analysis failed: {str(e)}")

@router.post("/pattern-library")
async def get_pattern_library(
    pattern_type: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Educational resource - descriptions of chart patterns.
    """
    patterns = {
        "reversal": [
            {
                "name": "Head and Shoulders",
                "type": "reversal",
                "reliability": "high",
                "description": "Three peaks with middle highest. Signals trend reversal.",
                "trading_approach": "Sell on neckline break, stop above right shoulder",
                "success_rate": "65-70%"
            },
            {
                "name": "Double Top",
                "type": "reversal",
                "reliability": "medium",
                "description": "Two peaks at similar resistance level.",
                "trading_approach": "Short on break of trough, target measured move",
                "success_rate": "60-65%"
            },
            {
                "name": "Inverse Head and Shoulders",
                "type": "reversal",
                "reliability": "high",
                "description": "Bullish reversal pattern, inverse of H&S",
                "trading_approach": "Buy on neckline break",
                "success_rate": "70%"
            }
        ],
        "continuation": [
            {
                "name": "Bull Flag",
                "type": "continuation",
                "reliability": "medium",
                "description": "Sharp rise followed by small consolidation channel.",
                "trading_approach": "Buy breakout of flag pole",
                "success_rate": "65%"
            },
            {
                "name": "Ascending Triangle",
                "type": "continuation",
                "reliability": "medium",
                "description": "Flat top with rising bottom trendline.",
                "trading_approach": "Buy breakout above resistance",
                "success_rate": "60-70%"
            }
        ],
        "candlestick": [
            {
                "name": "Engulfing Pattern",
                "type": "reversal",
                "reliability": "medium",
                "description": "Candle completely engulfs previous candle body.",
                "context_required": "Appears at trend extremes",
                "success_rate": "55-60%"
            },
            {
                "name": "Doji",
                "type": "indecision",
                "reliability": "low",
                "description": "Open and close nearly equal. Shows indecision.",
                "context_required": "Significant after strong trend",
                "success_rate": "Context dependent"
            }
        ]
    }
    
    if pattern_type:
        return patterns.get(pattern_type, [])
    
    return patterns

@router.get("/scan-multichart")
async def scan_multiple_timeframes(
    symbol: str,
    timeframes: List[str] = ["1H", "4H", "1D"],
    current_user = Depends(get_current_user)
):
    """
    Analyze confluence across multiple timeframes (requires data feed integration).
    """
    # This would integrate with your market data to fetch multiple timeframe charts
    # For now, returns structure
    return {
        "symbol": symbol,
        "timeframes_analyzed": timeframes,
        "confluence_score": 0.75,
        "alignment": "bullish",
        "recommendations": [
            {"timeframe": "1D", "bias": "bullish", "strength": "strong", "key_level": 1.0850},
            {"timeframe": "4H", "bias": "bullish", "strength": "moderate", "key_level": 1.0820},
            {"timeframe": "1H", "bias": "neutral", "strength": "weak", "key_level": 1.0840}
        ],
        "suggested_action": "Wait for 1H confirmation or pullback to 4H support"
    }
