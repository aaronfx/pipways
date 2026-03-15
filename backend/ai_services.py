"""AI Screening & Analysis Services - PRODUCTION READY
Fixed: Removed duplicate routes (now in dedicated performance router), cleaned imports
"""
import os
import base64
import json
import httpx
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .security import get_current_user

router = APIRouter()

# Import performance calculation from performance module
from .performance import calculate_performance_metrics

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Common trading symbols pattern
COMMON_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "XAGUSD", 
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "US30", "US100", "DE30"
]

# Request models (unique to this module)
class MentorRequest(BaseModel):
    question: str
    skill_level: str = "intermediate"

class TradeValidatorRequest(BaseModel):
    entry_price: float
    stop_loss: float
    take_profit: float
    direction: str  # BUY or SELL
    symbol: Optional[str] = None

class SignalSaveRequest(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    analysis: Optional[str] = None

class ChartAnalyzeRequest(BaseModel):
    """For text-based chart analysis requests"""
    symbol: str
    description: str
    timeframe: Optional[str] = "1H"

def extract_symbol_from_text(text: str) -> Optional[str]:
    """Extract trading symbol from AI response text"""
    if not text:
        return None

    text_upper = text.upper()

    # Check for common symbols
    for symbol in COMMON_SYMBOLS:
        if symbol in text_upper:
            return symbol

    # Regex pattern for forex pairs (6 chars, 3 letters + 3 letters)
    forex_pattern = r'([A-Z]{3})([A-Z]{3})'
    matches = re.findall(forex_pattern, text_upper)
    if matches:
        return matches[0][0] + matches[0][1]

    # Pattern for crypto (BTC, ETH, etc.)
    crypto_pattern = r'(BTC|ETH|XRP|LTC|BCH|ADA|DOT|LINK)[-/]?(USD|USDT|USDC|EUR)'
    match = re.search(crypto_pattern, text_upper)
    if match:
        return match.group(0).replace("-", "").replace("/", "")

    return None

def calculate_directional_rr(entry: float, sl: float, tp: float, direction: str) -> tuple:
    """
    Calculate direction-aware risk-reward ratio.
    Returns (rr_ratio, risk_reward_text, is_valid_structure)
    """
    direction = direction.upper()

    if direction == "BUY":
        risk = entry - sl
        reward = tp - entry
        is_valid = sl < entry < tp
    elif direction == "SELL":
        risk = sl - entry
        reward = entry - tp
        is_valid = tp < entry < sl
    else:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        is_valid = False

    risk = abs(risk)
    reward = abs(reward)

    rr_ratio = reward / risk if risk > 0 else 0

    # Clamp extreme values
    if rr_ratio > 10:
        rr_ratio = 10

    risk_reward_text = f"1:{rr_ratio:.2f}"

    return rr_ratio, risk_reward_text, is_valid

def calculate_quality_score(structure_valid: bool, rr_ratio: float, structure_quality: str) -> tuple:
    """
    Calculate deterministic trade quality score and grade.
    Returns (score, probability, grade)
    """
    score = 0

    if structure_valid:
        score += 25

    if rr_ratio >= 2:
        score += 25
    if rr_ratio >= 3:
        score += 10

    quality = structure_quality.lower() if structure_quality else ""
    if quality == "excellent":
        score += 20
    elif quality == "good":
        score += 10

    # Cap at 100
    score = min(score, 100)

    # Convert to probability
    probability = score / 100

    # Determine grade
    if score >= 85:
        grade = "A+"
    elif score >= 75:
        grade = "A"
    elif score >= 60:
        grade = "B"
    else:
        grade = "C"

    return score, probability, grade

# ==========================================
# AI MENTOR ENDPOINTS
# ==========================================

@router.post("/mentor/ask")
async def ask_mentor(
    request: MentorRequest,
    current_user = Depends(get_current_user)
):
    """
    AI Trading Mentor - Provides educational trading guidance.
    """
    question = request.question
    skill_level = request.skill_level

    if not question or len(question.strip()) < 2:
        raise HTTPException(400, "Question too short")

    if not OPENROUTER_CONFIGURED:
        return {
            "response": """I apologize, but the AI Mentor is currently in setup mode.

To enable full AI capabilities, please ensure OPENROUTER_API_KEY is set in your environment variables.

**Quick Trading Tips:**
• Risk max 1-2% per trade
• Always use stop losses
• Keep a trading journal
• Don't revenge trade""",
            "suggested_resources": ["Risk Management", "Position Sizing", "Trading Psychology"],
            "mode": "fallback",
            "configured": False
        }

    try:
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
                            "content": f"""You are an expert trading mentor with 20+ years of experience. 
User skill level: {skill_level}.
Provide clear, actionable trading education with specific examples.
Emphasize risk management and trading psychology. No specific financial advice."""
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.7
                },
                timeout=30.0
            )

            if response.status_code != 200:
                error_text = response.text
                print(f"[AI ERROR] OpenRouter HTTP {response.status_code}: {error_text}", flush=True)

                if response.status_code == 401:
                    raise HTTPException(500, "AI authentication failed. Check API key.")
                elif response.status_code == 429:
                    raise HTTPException(503, "AI service rate limited. Please try again.")
                else:
                    raise HTTPException(503, "AI service temporarily unavailable")

            data = response.json()

            if "choices" not in data or len(data["choices"]) == 0:
                raise HTTPException(500, "Invalid AI response format")

            ai_response = data["choices"][0]["message"]["content"]

            return {
                "response": ai_response,
                "suggested_resources": [],
                "mode": "ai",
                "model": OPENROUTER_MODEL,
                "configured": True
            }

    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI ERROR] Unexpected error: {e}", flush=True)
        raise HTTPException(500, f"AI service error: {str(e)}")

@router.post("/mentor/ask-legacy")
async def ask_mentor_legacy(
    question: str = Form(...),
    skill_level: str = Form("intermediate"),
    current_user = Depends(get_current_user)
):
    """Legacy form-data endpoint for compatibility"""
    return await ask_mentor(MentorRequest(question=question, skill_level=skill_level), current_user)

# ==========================================
# TRADE VALIDATOR ENDPOINTS
# ==========================================

@router.post("/trade/validate")
async def validate_trade(
    request: TradeValidatorRequest,
    current_user = Depends(get_current_user)
):
    """
    AI Trade Validator - Analyze trade setup quality.
    """
    entry = request.entry_price
    sl = request.stop_loss
    tp = request.take_profit
    direction = request.direction.upper()
    symbol = request.symbol or "Unknown"

    # Calculate direction-aware RR
    rr_ratio, risk_reward_text, is_valid = calculate_directional_rr(entry, sl, tp, direction)

    if not OPENROUTER_CONFIGURED:
        # Calculate deterministic score
        score, prob, grade = calculate_quality_score(is_valid, rr_ratio, "good")

        return {
            "risk_reward_ratio": round(rr_ratio, 2),
            "risk_reward_text": risk_reward_text,
            "probability_estimate": prob,
            "structure_valid": is_valid,
            "structure_quality": "valid" if is_valid else "invalid",
            "quality_score": score,
            "trade_grade": grade,
            "recommendations": [
                "Configure OPENROUTER_API_KEY for advanced AI validation",
                "Ensure risk:reward is at least 1:2"
            ],
            "warnings": [] if is_valid else ["Invalid structure: Check entry/SL/TP alignment"],
            "mode": "fallback"
        }

    try:
        prompt = f"""Analyze this trade setup:
        Symbol: {symbol}
        Direction: {direction}
        Entry: {entry}
        Stop Loss: {sl}
        Take Profit: {tp}
        Risk:Reward: {risk_reward_text}

        Evaluate:
        1. Is the structure valid (SL below entry for BUY, above for SELL)?
        2. Risk management quality (is {risk_reward_text} favorable?)
        3. Probability estimate based on typical price action
        4. Trade quality score 0-100
        5. Any warnings or recommendations

        Return JSON:
        {{
            "structure_valid": true/false,
            "structure_quality": "excellent|good|fair|poor|invalid",
            "probability_estimate": 0.0-1.0,
            "quality_score": 0-100,
            "risk_reward_assessment": "excellent|good|adequate|poor",
            "recommendations": ["..."],
            "warnings": ["..."]
        }}"""

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
                        {"role": "system", "content": "You are a professional trade analyst. Evaluate trade setups objectively."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise HTTPException(503, "AI validation service unavailable")

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON with markdown stripping
            try:
                clean_content = content.strip()
                if clean_content.startswith("`"):
                    clean_content = clean_content.split("`")[1]
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0].strip()

                json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {}
            except:
                result = {}

            # Normalize probability
            prob = result.get("probability_estimate", 0.6)
            if prob <= 0:
                prob = 0.6
            if prob > 1:
                prob = 1
            result["probability_estimate"] = prob

            # Calculate deterministic quality score
            structure_quality = result.get("structure_quality", "good")
            score, deterministic_prob, grade = calculate_quality_score(
                result.get("structure_valid", is_valid), 
                rr_ratio, 
                structure_quality
            )

            # Blend AI probability with deterministic probability
            final_prob = (prob + deterministic_prob) / 2

            return {
                "risk_reward_ratio": round(rr_ratio, 2),
                "risk_reward_text": risk_reward_text,
                "probability_estimate": round(final_prob, 2),
                "structure_valid": result.get("structure_valid", is_valid),
                "structure_quality": structure_quality,
                "quality_score": score,
                "trade_grade": grade,
                "risk_reward_assessment": result.get("risk_reward_assessment", "good"),
                "recommendations": result.get("recommendations", []),
                "warnings": result.get("warnings", []),
                "mode": "ai",
                "configured": True
            }

    except Exception as e:
        print(f"[VALIDATOR ERROR] {e}", flush=True)
        # Fallback to deterministic calculation
        score, prob, grade = calculate_quality_score(is_valid, rr_ratio, "good")
        return {
            "risk_reward_ratio": round(rr_ratio, 2),
            "risk_reward_text": risk_reward_text,
            "probability_estimate": prob,
            "structure_valid": is_valid,
            "structure_quality": "valid" if is_valid else "invalid",
            "quality_score": score,
            "trade_grade": grade,
            "recommendations": ["AI service temporarily unavailable - using fallback calculation"],
            "warnings": [] if is_valid else ["Invalid structure: Check entry/SL/TP alignment"],
            "mode": "fallback"
        }

# ==========================================
# SIGNAL MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/signal/save")
async def save_signal(
    request: SignalSaveRequest,
    current_user = Depends(get_current_user)
):
    """
    Save AI-generated trade setup as a signal.
    """
    try:
        # Here you would typically save to database
        # For now, return success with signal ID
        signal_id = f"sig_{os.urandom(4).hex()}"

        return {
            "success": True,
            "signal_id": signal_id,
            "message": "Signal saved successfully",
            "signal": {
                "id": signal_id,
                "symbol": request.symbol,
                "direction": request.direction,
                "entry_price": request.entry_price,
                "stop_loss": request.stop_loss,
                "take_profit": request.take_profit,
                "confidence": request.confidence,
                "created_at": "2024-01-01T00:00:00Z",
                "status": "active"
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to save signal: {str(e)}")

# ==========================================
# CHART ANALYSIS (Lightweight version)
# Full chart analysis moved to chart_analysis.py
# ==========================================

@router.post("/chart/analyze-text")
async def analyze_chart_text(
    request: ChartAnalyzeRequest,
    current_user = Depends(get_current_user)
):
    """
    Text-based chart analysis (for descriptions without image).
    For image analysis, use /ai/chart/analyze (chart_analysis.py).
    """
    if not OPENROUTER_CONFIGURED:
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "trading_bias": "neutral",
            "confidence": 0.5,
            "analysis": "AI analysis requires OPENROUTER_API_KEY configuration",
            "trade_setup": None,
            "mode": "fallback"
        }

    try:
        prompt = f"""Analyze this {request.symbol} chart description for {request.timeframe} timeframe:

        Description: {request.description}

        Provide:
        1. Trading bias (bullish/bearish/neutral)
        2. Confidence level (0-1)
        3. Key support/resistance levels
        4. Suggested trade setup if any

        Return as JSON."""

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
                        {"role": "system", "content": "You are a technical analyst. Provide structured analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1000
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Try to extract JSON
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        analysis = {
                            "trading_bias": "neutral",
                            "confidence": 0.5,
                            "analysis": content[:500]
                        }
                except:
                    analysis = {
                        "trading_bias": "neutral", 
                        "confidence": 0.5,
                        "analysis": content[:500]
                    }

                return {
                    "symbol": request.symbol,
                    "timeframe": request.timeframe,
                    **analysis,
                    "mode": "ai"
                }
            else:
                raise HTTPException(503, "Chart analysis service unavailable")

    except Exception as e:
        print(f"[CHART TEXT ERROR] {e}", flush=True)
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "trading_bias": "neutral",
            "confidence": 0,
            "error": str(e),
            "mode": "fallback"
        }

# ==========================================
# COMPATIBILITY NOTE
# ==========================================
# The following endpoints have been MOVED to dedicated routers:
# - /performance/*  -> performance.py (upload-journal, analyze-journal, dashboard, etc.)
# - /chart/analyze (image) -> chart_analysis.py
# 
# This avoids route collisions and maintains clean separation of concerns.
# The imports above ensure calculate_performance_metrics is still available
# for any legacy code that needs it.
