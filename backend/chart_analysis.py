"""
AI Chart Analysis - PRODUCTION READY
Uses OpenRouter Vision API (Claude 3.5 Sonnet via OpenRouter)
Smart Money Concepts (SMC) Institutional Analysis Engine
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "US30", "US100", "DE30", "DXY"
]

def normalize_symbol(symbol: str) -> str:
    """Normalize detected trading symbol to standard format"""
    if not symbol:
        return "Unknown"
    
    symbol_clean = symbol.upper().strip()
    
    # Remove separators and spaces
    symbol_clean = symbol_clean.replace("/", "").replace("-", "").replace(" ", "").replace(".", "")
    
    # Normalization mappings for common assets
    mappings = {
        "GOLD": "XAUUSD",
        "XAU": "XAUUSD", 
        "SILVER": "XAGUSD",
        "XAG": "XAGUSD",
        "BITCOIN": "BTCUSD",
        "BTC": "BTCUSD",
        "ETHEREUM": "ETHUSD",
        "ETH": "ETHUSD",
        "US30": "US30",
        "US100": "US100",
        "NAS100": "US100",
        "NAS": "US100",
        "NASDAQ": "US100",
        "SP500": "US500",
        "SPX": "US500",
        "DXY": "DXY",
        "DOLLARINDEX": "DXY",
        "USDOLLARINDEX": "DXY",
        "USDX": "DXY",
        "U.S.DOLLARINDEX": "DXY",
        "U.S.DOLLAR": "DXY",
        "GER30": "DE30",
        "DE30": "DE30",
        "UK100": "UK100",
        "JP225": "JP225",
        "AUS200": "AU200",
    }
    
    # Check exact match
    if symbol_clean in mappings:
        return mappings[symbol_clean]
    
    # Check for common forex patterns (6 chars)
    if len(symbol_clean) == 6 and symbol_clean.isalpha():
        return symbol_clean
    
    return symbol_clean

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
    Smart Money Concepts Chart Analysis using OpenRouter Vision API.
    Returns institutional-grade analysis with SMC signals and annotations.
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
            demo_symbol = normalize_symbol(symbol or "EURUSD")
            return {
                "symbol": demo_symbol,
                "market_structure": "bullish",
                "smc_signals": ["liquidity sweep below equal lows", "bullish order block formed"],
                "trading_bias": "bullish",
                "confidence": 0.82,
                "patterns_detected": [
                    {"name": "Bullish Order Block", "reliability": "high"},
                    {"name": "Fair Value Gap", "reliability": "medium"}
                ],
                "support_levels": ["1.0850", "1.0820"],
                "resistance_levels": ["1.0950", "1.1000"],
                "suggested_entry": "1.0860",
                "suggested_stop": "1.0830",
                "suggested_target": "1.0950",
                "risk_reward_ratio": "1:3",
                "key_insights": [
                    f"{demo_symbol} showing bullish market structure with BOS",
                    "Liquidity sweep below equal lows - institutional buying detected",
                    "Fair value gap indicates strong buying pressure"
                ],
                "chart_image": f"data:{content_type};base64,{base64_image}",
                "chart_annotations": {
                    "bos_levels": ["1.0850"],
                    "liquidity_zones": [{"price": "1.0820", "type": "equal_lows"}],
                    "order_blocks": [{"price": "1.0840", "type": "bullish", "timeframe": "1H"}],
                    "fair_value_gaps": [{"start": "1.0860", "end": "1.0875", "type": "bullish"}],
                    "premium_discount": {"current": "discount", "range": ["1.0820", "1.0950"]}
                },
                "trade_setup": {
                    "entry": "1.0860",
                    "stop_loss": "1.0830",
                    "take_profit": "1.0950",
                    "risk_reward": "1:3",
                    "probability": 0.82,
                    "direction": "BUY",
                    "setup_type": "SMC Institutional"
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

        system_prompt = """You are a professional institutional trader specializing in Smart Money Concepts (SMC). Analyze this trading chart like a prop firm trader using hedge-fund grade analysis.

Detect and identify:

MARKET STRUCTURE
• Higher Highs / Higher Lows (HH/HL) for bullish structure
• Lower Highs / Lower Lows (LH/LL) for bearish structure  
• Break of Structure (BOS) - price breaking previous high/low confirming trend
• Change of Character (CHOCH) - structure shift from bullish to bearish or vice versa

LIQUIDITY ZONES
• Equal highs / equal lows (liquidity pools where stops cluster)
• Liquidity sweeps/grabs (price taking out highs/lows before reversing)
• Stop hunts (institutional manipulation of retail stops)

INSTITUTIONAL FOOTPRINT
• Order Blocks (OB) - last opposing candle before aggressive move, bullish/bearish
• Fair Value Gaps (FVG) - 3-candle pattern with gap between candle 1 and 3 wicks
• Imbalances - areas where price moved too fast, leaving unfilled orders

VALUATION ZONES
• Premium zones (above mid-point of dealing range, expensive for buyers)
• Discount zones (below mid-point of dealing range, cheap for buyers)
• Equilibrium (fair value mid-point)

TRADE SETUP
• High-probability institutional trade setups with confluence
• Optimal entry points at discount/premium + OB + FVG confluence
• Logical stop loss placement (beyond structure, beyond liquidity)
• Take profit targets (next liquidity pool, opposing order block, or 1:2/1:3 RR)

You MUST return analysis in this STRICT JSON format:
{
    "symbol": "detected symbol like EURUSD or DXY",
    "market_structure": "bullish|bearish|ranging",
    "smc_signals": ["signal 1", "signal 2", "signal 3"],
    "patterns_detected": [{"name": "pattern name", "reliability": "high|medium|low"}],
    "chart_annotations": {
        "bos_levels": ["price1", "price2"],
        "liquidity_zones": [{"price": "price", "type": "equal_highs|equal_lows"}],
        "order_blocks": [{"price": "price", "type": "bullish|bearish", "timeframe": "1H|4H|Daily"}],
        "fair_value_gaps": [{"start": "price1", "end": "price2", "type": "bullish|bearish"}],
        "premium_discount": {"current": "premium|discount|equilibrium", "range": ["low", "high"]}
    },
    "support_levels": ["price1", "price2"],
    "resistance_levels": ["price1", "price2"],
    "suggested_entry": "price",
    "suggested_stop": "price",
    "suggested_target": "price",
    "trading_bias": "bullish|bearish|neutral",
    "confidence": 0.0-1.0,
    "risk_reward_ratio": "1:2.5",
    "key_insights": ["insight 1", "insight 2", "insight 3"],
    "structure_quality": "strong|weak|neutral"
}

Be precise with price levels to 4-5 decimal places for forex, whole numbers for indices. Return ONLY valid JSON. No markdown, no explanation."""

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
                                    "text": f"Analyze this trading chart using Smart Money Concepts institutional methodology. {symbol_context}. {timeframe_context}. Detect symbol, market structure, liquidity zones, order blocks, fair value gaps, and provide high-probability trade setup. Return STRICT JSON only."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_url, "detail": "high"}
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2500,
                    "temperature": 0.1
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
                # Clean up potential markdown
                clean_content = content.strip()
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0].strip()
                
                result = json.loads(clean_content)
            except json.JSONDecodeError:
                print(f"[CHART ANALYSIS] JSON parse failed, content: {content[:300]}", flush=True)
                detected_symbol = extract_symbol_from_text(content) or symbol or "Unknown"
                result = {
                    "symbol": detected_symbol,
                    "market_structure": "neutral",
                    "smc_signals": [],
                    "patterns_detected": [],
                    "chart_annotations": {},
                    "support_levels": [],
                    "resistance_levels": [],
                    "suggested_entry": None,
                    "suggested_stop": None,
                    "suggested_target": None,
                    "trading_bias": "neutral",
                    "confidence": 0,
                    "key_insights": [content[:200]],
                    "structure_quality": "neutral"
                }

            # Ensure symbol and normalize it
            detected_symbol = result.get("symbol") or symbol or "Unknown"
            result["symbol"] = normalize_symbol(detected_symbol)

            # Ensure chart_annotations exists
            if "chart_annotations" not in result or not result["chart_annotations"]:
                result["chart_annotations"] = {
                    "bos_levels": [],
                    "liquidity_zones": [],
                    "order_blocks": [],
                    "fair_value_gaps": [],
                    "premium_discount": {}
                }

            # Add chart image to result
            result["chart_image"] = f"data:{content_type};base64,{base64_image}"

            # Build trade setup if not present but we have levels
            if not result.get("trade_setup") or not result["trade_setup"].get("entry"):
                if result.get("suggested_entry") and result.get("suggested_stop") and result.get("suggested_target"):
                    try:
                        entry = float(str(result["suggested_entry"]).replace(",", ""))
                        sl = float(str(result["suggested_stop"]).replace(",", ""))
                        tp = float(str(result["suggested_target"]).replace(",", ""))

                        risk = abs(entry - sl)
                        reward = abs(tp - entry)
                        rr = f"1:{reward/risk:.1f}" if risk > 0 else "N/A"
                        direction = "BUY" if result.get("trading_bias") == "bullish" else "SELL" if result.get("trading_bias") == "bearish" else "NEUTRAL"

                        result["trade_setup"] = {
                            "entry": str(entry),
                            "stop_loss": str(sl),
                            "take_profit": str(tp),
                            "risk_reward": rr,
                            "probability": result.get("confidence", 0.7),
                            "direction": direction,
                            "setup_type": "SMC Institutional",
                            "quality": result.get("structure_quality", "neutral")
                        }
                    except:
                        result["trade_setup"] = None
                else:
                    result["trade_setup"] = None

            # Ensure risk_reward_ratio exists
            if not result.get("risk_reward_ratio") and result.get("trade_setup"):
                result["risk_reward_ratio"] = result["trade_setup"].get("risk_reward", "N/A")

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
    """Educational pattern library with SMC concepts"""
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
        ],
        "smc": [
            {"name": "Order Block", "type": "smc", "reliability": "high", "description": "Last opposing candle before strong move", "success_rate": "70%"},
            {"name": "Fair Value Gap", "type": "smc", "reliability": "high", "description": "Imbalance zone between candles", "success_rate": "68%"},
            {"name": "Liquidity Sweep", "type": "smc", "reliability": "high", "description": "Stop hunt above/below equal highs/lows", "success_rate": "75%"},
            {"name": "Break of Structure", "type": "smc", "reliability": "medium", "description": "Price breaking previous high/low", "success_rate": "65%"},
            {"name": "Change of Character", "type": "smc", "reliability": "high", "description": "Market structure shift", "success_rate": "72%"}
        ]
    }
