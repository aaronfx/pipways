"""
AI Services API - PRODUCTION READY (OpenRouter/Claude)
Handles AI Mentor chat and Chart Analysis using OpenRouter
"""
import os
import base64
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, List
import httpx
from .security import get_current_user

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

@router.post("/mentor/ask")
async def ask_mentor(
    question: str,
    skill_level: str = "intermediate",
    current_user = Depends(get_current_user)
):
    """
    AI Trading Mentor endpoint using OpenRouter (Claude/GPT-4).
    """
    if not OPENROUTER_CONFIGURED:
        return {
            "response": """I apologize, but the AI Mentor service is not configured.

To enable AI capabilities, please set:
- OPENROUTER_API_KEY (your OpenRouter key from openrouter.ai)
- OPENROUTER_MODEL (e.g., anthropic/claude-3.5-sonnet)

In the meantime, here are trading best practices:
• Risk max 1-2% per trade
• Always use stop losses
• Keep a trading journal
• Don't revenge trade""",
            "suggested_resources": ["Risk Management", "Position Sizing", "Trading Psychology"],
            "mode": "fallback"
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
                            "content": f"""You are an expert trading mentor and financial educator. 
You help traders improve their skills in forex, crypto, and stock trading.
The user's skill level is: {skill_level}.
Provide clear, actionable advice. Always emphasize risk management.
Never give specific financial advice for particular trades, only educational guidance."""
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"[AI ERROR] OpenRouter returned {response.status_code}: {response.text}", flush=True)
                raise HTTPException(500, "AI service temporarily unavailable")
            
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            # Extract suggested resources from the response
            suggested_resources = []
            if "risk" in ai_response.lower():
                suggested_resources.append("Risk Management")
            if "psychology" in ai_response.lower() or "emotion" in ai_response.lower():
                suggested_resources.append("Trading Psychology")
            if "technical" in ai_response.lower() or "chart" in ai_response.lower():
                suggested_resources.append("Technical Analysis")
            if "position" in ai_response.lower() or "size" in ai_response.lower():
                suggested_resources.append("Position Sizing")
            
            return {
                "response": ai_response,
                "suggested_resources": suggested_resources[:3],
                "model": OPENROUTER_MODEL,
                "mode": "ai"
            }
            
    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Please try again.")
    except Exception as e:
        print(f"[AI ERROR] Mentor failed: {e}", flush=True)
        raise HTTPException(500, "AI service error. Please try again later.")

@router.post("/chart/analyze")
async def analyze_chart(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """
    Chart Analysis using Claude Vision via OpenRouter.
    Analyzes uploaded chart image for patterns, support/resistance, and trade setups.
    """
    if not OPENROUTER_CONFIGURED:
        # Return demo analysis when not configured
        demo_symbol = symbol or "EURUSD"
        
        return {
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
            "risk_reward_ratio": "1:2.7",
            "key_insights": [
                f"{demo_symbol} showing consolidation at support",
                "Wait for breakout confirmation",
                "Risk management crucial here",
                "Set alerts for key levels",
                "Demo mode: Add OPENROUTER_API_KEY for AI analysis"
            ],
            "mode": "demo"
        }
    
    try:
        # Read and encode image
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(413, "File too large. Max 10MB.")
        
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Determine mime type
        content_type = file.content_type or "image/jpeg"
        if not content_type.startswith('image/'):
            raise HTTPException(400, "Only image files accepted")
        
        data_url = f"data:{content_type};base64,{base64_image}"
        
        symbol_context = f"Symbol: {symbol}" if symbol else "Symbol: Unknown"
        timeframe_context = f"Timeframe: {timeframe}" if timeframe else "Timeframe: Unknown"
        
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
                    "model": OPENROUTER_VISION_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a professional technical analyst. Analyze the trading chart image and provide:
1. Trading bias (bullish/bearish/neutral)
2. Confidence level (0-1)
3. Patterns detected with reliability (high/medium/low)
4. Key support levels (2-3 prices)
5. Key resistance levels (2-3 prices)
6. Suggested trade levels (entry, stop loss, take profit)
7. Key insights (3-5 bullet points)

Respond ONLY in valid JSON format with these exact keys:
{
  "trading_bias": "bullish|bearish|neutral",
  "confidence": 0.85,
  "patterns_detected": [{"name": "...", "reliability": "high|medium|low"}],
  "support_levels": ["1.0850"],
  "resistance_levels": ["1.0950"],
  "suggested_entry": "1.0860",
  "suggested_stop": "1.0830",
  "suggested_target": "1.0940",
  "key_insights": ["...", "..."]
}"""
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Analyze this trading chart. {symbol_context}. {timeframe_context}. Identify patterns, support/resistance, and suggest trade levels with risk management."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": data_url
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2
                },
                timeout=60.0  # Vision takes longer
            )
            
            if response.status_code != 200:
                print(f"[AI ERROR] OpenRouter Vision returned {response.status_code}: {response.text}", flush=True)
                raise HTTPException(500, "Chart analysis service error")
            
            data = response.json()
            ai_content = data["choices"][0]["message"]["content"]
            
            # Try to parse JSON from response
            try:
                # Clean up response - remove markdown code blocks if present
                clean_content = ai_content
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0]
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0]
                
                analysis = json.loads(clean_content.strip())
                
                # Validate required fields
                required_fields = ["trading_bias", "patterns_detected", "support_levels", 
                                 "resistance_levels", "suggested_entry", "suggested_stop", 
                                 "suggested_target", "key_insights"]
                
                for field in required_fields:
                    if field not in analysis:
                        analysis[field] = [] if "detected" in field or "levels" in field or "insights" in field else "N/A"
                
                analysis["mode"] = "ai"
                analysis["model"] = OPENROUTER_VISION_MODEL
                
                return analysis
                
            except json.JSONDecodeError as e:
                print(f"[AI ERROR] Failed to parse JSON response: {e}", flush=True)
                print(f"[AI ERROR] Raw content: {ai_content}", flush=True)
                
                # Fallback: return raw response formatted
                return {
                    "trading_bias": "neutral",
                    "confidence": 0.5,
                    "patterns_detected": [{"name": "Analysis completed", "reliability": "medium"}],
                    "support_levels": ["N/A"],
                    "resistance_levels": ["N/A"],
                    "suggested_entry": "N/A",
                    "suggested_stop": "N/A",
                    "suggested_target": "N/A",
                    "key_insights": [ai_content[:200] + "..."],
                    "mode": "raw"
                }
                
    except httpx.TimeoutException:
        raise HTTPException(504, "Chart analysis timed out. Please try with a smaller image.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI ERROR] Chart analysis failed: {e}", flush=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")
