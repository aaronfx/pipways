"""AI Screening & Analysis Services - PRODUCTION READY"""
import os
import base64
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from .security import get_current_user

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Request models
class MentorRequest(BaseModel):
    question: str
    skill_level: str = "intermediate"

@router.post("/mentor/ask")
async def ask_mentor(
    request: MentorRequest,
    current_user = Depends(get_current_user)
):
    """
    AI Trading Mentor - Provides educational trading guidance.
    Accepts JSON: {"question": "how do I trade?", "skill_level": "intermediate"}
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

@router.post("/chart/analyze")
async def analyze_chart(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """Chart Analysis using Claude Vision"""
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Invalid file type. Allowed: {', '.join(allowed_types)}")
    
    if not OPENROUTER_CONFIGURED:
        return {
            "trading_bias": "neutral",
            "confidence": 0.75,
            "patterns_detected": [
                {"name": "Support Test", "reliability": "medium"}
            ],
            "support_levels": ["1.0850"],
            "resistance_levels": ["1.0950"],
            "suggested_entry": "1.0860",
            "suggested_stop": "1.0830",
            "suggested_target": "1.0940",
            "key_insights": ["Demo mode - configure OPENROUTER_API_KEY"],
            "mode": "demo",
            "configured": False
        }
    
    try:
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(400, "Empty file uploaded")
            
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(413, "File too large. Maximum size is 10MB.")
        
        base64_image = base64.b64encode(contents).decode('utf-8')
        content_type = file.content_type or "image/jpeg"
        data_url = f"data:{content_type};base64,{base64_image}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://pipwaysapp.onrender.com",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": """Analyze this trading chart. Respond in JSON format with: trading_bias, confidence, patterns_detected, support_levels, resistance_levels, suggested_entry, suggested_stop, suggested_target, key_insights"""
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
                raise HTTPException(503, "Chart analysis service error")
            
            data = response.json()
            ai_content = data["choices"][0]["message"]["content"]
            
            try:
                clean_content = ai_content.strip()
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(clean_content)
                analysis["mode"] = "ai"
                return analysis
                
            except json.JSONDecodeError:
                return {
                    "trading_bias": "neutral",
                    "confidence": 0.5,
                    "patterns_detected": [],
                    "support_levels": [],
                    "resistance_levels": [],
                    "key_insights": [ai_content[:300]],
                    "mode": "raw"
                }
                
    except Exception as e:
        print(f"[AI ERROR] Chart analysis: {e}", flush=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")
