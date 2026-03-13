"""
AI Services API - PRODUCTION READY
Uses OpenRouter for Claude/GPT-4 access
"""
import os
import base64
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, List
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
    AI Trading Mentor endpoint using OpenRouter (Claude).
    """
    if not OPENROUTER_CONFIGURED:
        return {
            "response": """I apologize, but the AI Mentor service is not configured.

To enable AI capabilities, please set:
- OPENROUTER_API_KEY (your key from openrouter.ai)
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
                            "content": f"""You are an expert trading mentor. 
User skill level: {skill_level}.
Provide clear, actionable trading education.
Emphasize risk management. No specific financial advice."""
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
                print(f"[AI ERROR] OpenRouter returned {response.status_code}", flush=True)
                raise HTTPException(500, "AI service error")
            
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            return {
                "response": ai_response,
                "suggested_resources": [],
                "mode": "ai"
            }
            
    except Exception as e:
        print(f"[AI ERROR] Mentor failed: {e}", flush=True)
        raise HTTPException(500, "AI service error")

@router.post("/chart/analyze")
async def analyze_chart(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """
    Chart Analysis using Claude Vision via OpenRouter.
    """
    if not OPENROUTER_CONFIGURED:
        return {
            "trading_bias": "neutral",
            "confidence": 0.75,
            "patterns_detected": [{"name": "Demo Mode", "reliability": "medium"}],
            "support_levels": ["1.0850"],
            "resistance_levels": ["1.0950"],
            "suggested_entry": "1.0860",
            "suggested_stop": "1.0830",
            "suggested_target": "1.0940",
            "key_insights": ["Add OPENROUTER_API_KEY for AI analysis"],
            "mode": "demo"
        }
    
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(413, "File too large. Max 10MB.")
        
        base64_image = base64.b64encode(contents).decode('utf-8')
        content_type = file.content_type or "image/jpeg"
        data_url = f"data:{content_type};base64,{base64_image}"
        
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
                            "content": """Analyze this trading chart. Respond in JSON:
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
                                    "text": f"Analyze this chart. Symbol: {symbol or 'Unknown'}. Timeframe: {timeframe or 'Unknown'}"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_url}
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.2
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(500, "Chart analysis error")
            
            data = response.json()
            ai_content = data["choices"][0]["message"]["content"]
            
            # Parse JSON response
            try:
                clean_content = ai_content
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0]
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0]
                
                analysis = json.loads(clean_content.strip())
                analysis["mode"] = "ai"
                return analysis
                
            except json.JSONDecodeError:
                return {
                    "trading_bias": "neutral",
                    "confidence": 0.5,
                    "patterns_detected": [],
                    "support_levels": [],
                    "resistance_levels": [],
                    "suggested_entry": "N/A",
                    "suggested_stop": "N/A",
                    "suggested_target": "N/A",
                    "key_insights": [ai_content[:200]],
                    "mode": "raw"
                }
                
    except Exception as e:
        print(f"[AI ERROR] Chart analysis failed: {e}", flush=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")
