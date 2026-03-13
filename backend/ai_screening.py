"""
AI Screening & Analysis Services
Handles AI Mentor chat and Chart Analysis using OpenRouter (Claude/GPT-4)
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

# ==========================================
# AI MENTOR ENDPOINTS
# ==========================================

@router.post("/mentor/ask")
async def ask_mentor(
    question: str,
    skill_level: str = "intermediate",
    current_user = Depends(get_current_user)
):
    """
    AI Trading Mentor - Provides educational trading guidance.
    Uses Claude via OpenRouter when configured, otherwise returns helpful fallback.
    """
    # Validate input
    if not question or len(question.strip()) < 3:
        raise HTTPException(400, "Question too short")
    
    if not OPENROUTER_CONFIGURED:
        return {
            "response": """I apologize, but the AI Mentor is currently in setup mode.

To enable full AI capabilities, please ensure OPENROUTER_API_KEY is set in your environment variables.

**Quick Trading Tips:**
• **Risk Management**: Never risk more than 1-2% of your account per trade
• **Position Sizing**: Calculate based on your stop loss distance and account size
• **Trading Psychology**: Keep a detailed journal to track emotions and patterns
• **Technical Analysis**: Look for confluence between multiple timeframes and indicators
• **Discipline**: Stick to your trading plan, avoid revenge trading

Once OpenRouter is configured, I'll provide personalized, detailed responses to your specific trading questions!""",
            "suggested_resources": [
                "Risk Management Guide",
                "Position Sizing Calculator", 
                "Trading Psychology Masterclass",
                "Technical Analysis Basics"
            ],
            "mode": "fallback",
            "configured": False
        }
    
    # Call OpenRouter API
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
                            "content": f"""You are an expert trading mentor and financial educator for the Pipways platform.

TRADER PROFILE:
- Skill Level: {skill_level}
- Platform: Professional trading signals and education

GUIDELINES:
1. Provide educational guidance only - never specific buy/sell recommendations
2. Emphasize risk management in every response
3. Use clear, actionable language
4. Reference technical analysis concepts when relevant
5. Keep responses concise but informative (2-4 paragraphs max)
6. Always include a risk management reminder

TOPICS YOU COVER:
- Forex, Crypto, and Stock trading strategies
- Risk management and position sizing
- Trading psychology and emotional control
- Technical analysis (support/resistance, patterns, indicators)
- Fundamental analysis basics
- Trading journal and performance review

RESPONSE FORMAT:
- Direct answer to the question
- Practical application tip
- Risk management reminder"""
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
                error_detail = response.text
                print(f"[AI ERROR] OpenRouter HTTP {response.status_code}: {error_detail}", flush=True)
                
                if response.status_code == 401:
                    raise HTTPException(500, "AI authentication failed. Check OPENROUTER_API_KEY.")
                elif response.status_code == 429:
                    raise HTTPException(503, "AI service rate limited. Please try again shortly.")
                else:
                    raise HTTPException(503, "AI service temporarily unavailable")
            
            data = response.json()
            
            # Validate response structure
            if "choices" not in data or len(data["choices"]) == 0:
                raise HTTPException(500, "Invalid AI response format")
            
            ai_response = data["choices"][0]["message"]["content"]
            
            # Extract suggested resources based on content
            suggested_resources = []
            content_lower = ai_response.lower()
            
            if any(word in content_lower for word in ["risk", "stop loss", "position size"]):
                suggested_resources.append("Risk Management")
            if any(word in content_lower for word in ["psychology", "emotion", "discipline", "mindset"]):
                suggested_resources.append("Trading Psychology")
            if any(word in content_lower for word in ["chart", "pattern", "support", "resistance", "indicator"]):
                suggested_resources.append("Technical Analysis")
            if any(word in content_lower for word in ["fundamental", "news", "economic", "fed", "interest"]):
                suggested_resources.append("Fundamental Analysis")
            if any(word in content_lower for word in ["journal", "review", "analyze performance"]):
                suggested_resources.append("Performance Analytics")
            
            return {
                "response": ai_response,
                "suggested_resources": suggested_resources[:3],
                "mode": "ai",
                "model": OPENROUTER_MODEL,
                "configured": True
            }
            
    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Please try again.")
    except httpx.ConnectError:
        raise HTTPException(503, "Cannot connect to AI service. Please try again later.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI ERROR] Unexpected error: {e}", flush=True)
        raise HTTPException(500, "AI service encountered an error")

@router.get("/mentor/daily-wisdom")
async def get_daily_wisdom(current_user = Depends(get_current_user)):
    """Get daily trading wisdom/quote"""
    import random
    
    wisdom_quotes = [
        {"quote": "Cut losses short, let profits run.", "author": "Trading Proverb"},
        {"quote": "The goal of a successful trader is to make the best trades. Money is secondary.", "author": "Alexander Elder"},
        {"quote": "Markets can remain irrational longer than you can remain solvent.", "author": "John Maynard Keynes"},
        {"quote": "Risk comes from not knowing what you're doing.", "author": "Warren Buffett"},
        {"quote": "The four most dangerous words in investing are: 'This time it's different'.", "author": "Sir John Templeton"},
        {"quote": "Plan your trade and trade your plan.", "author": "Trading Proverb"},
        {"quote": "Do not anticipate and move without market confirmation—being a little late in your trade is your insurance.", "author": "Jesse Livermore"}
    ]
    
    return random.choice(wisdom_quotes)

# ==========================================
# CHART ANALYSIS ENDPOINTS
# ==========================================

@router.post("/chart/analyze")
async def analyze_chart(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """
    AI Chart Analysis using Claude Vision.
    Analyzes uploaded chart image for patterns, levels, and trade setups.
    """
    # Validate file
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Invalid file type. Allowed: {', '.join(allowed_types)}")
    
    if not OPENROUTER_CONFIGURED:
        # Return demo analysis when API not configured
        demo_symbol = symbol or "EURUSD"
        demo_tf = timeframe or "1H"
        
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
                f"{demo_symbol} on {demo_tf} showing consolidation at support level",
                "Volume profile suggests accumulation pattern",
                "Wait for clear breakout confirmation before entry",
                "Key resistance at 1.0950 needs to break for bullish continuation",
                "Demo mode: Configure OPENROUTER_API_KEY for AI-powered analysis"
            ],
            "mode": "demo",
            "configured": False
        }
    
    try:
        # Read and validate image
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(400, "Empty file uploaded")
            
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(413, "File too large. Maximum size is 10MB.")
        
        # Encode to base64
        base64_image = base64.b64encode(contents).decode('utf-8')
        content_type = file.content_type or "image/jpeg"
        data_url = f"data:{content_type};base64,{base64_image}"
        
        # Prepare context
        symbol_context = f"Trading Pair/Symbol: {symbol}" if symbol else "Symbol: Not specified"
        timeframe_context = f"Timeframe: {timeframe}" if timeframe else "Timeframe: Not specified"
        
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
                            "content": """You are a professional technical analyst specializing in forex, crypto, and stock charts.

Analyze the provided chart image and respond ONLY with valid JSON in this exact format:

{
  "trading_bias": "bullish" or "bearish" or "neutral",
  "confidence": 0.0 to 1.0,
  "patterns_detected": [
    {"name": "pattern name", "reliability": "high|medium|low"}
  ],
  "support_levels": ["price1", "price2"],
  "resistance_levels": ["price1", "price2"],
  "suggested_entry": "price or null",
  "suggested_stop": "price or null",
  "suggested_target": "price or null",
  "key_insights": ["insight 1", "insight 2", "insight 3"]
}

GUIDELINES:
- Identify 1-3 clear chart patterns if present
- Mark 2-3 support and resistance levels
- Suggest trade levels only if setup is clear
- Include risk management warnings in insights
- Be specific about price levels visible in chart
- If unclear, state "unclear" for bias and give general observations"""
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Analyze this trading chart.\n\n{symbol_context}\n{timeframe_context}\n\nIdentify patterns, key levels (support/resistance), and suggest trade setup if applicable. Emphasize risk management."
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
                    "max_tokens": 2000,
                    "temperature": 0.2
                },
                timeout=60.0  # Vision takes longer
            )
            
            if response.status_code != 200:
                print(f"[AI ERROR] Vision API HTTP {response.status_code}: {response.text}", flush=True)
                raise HTTPException(503, "Chart analysis service error")
            
            data = response.json()
            ai_content = data["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            try:
                # Clean up markdown formatting if present
                clean_content = ai_content.strip()
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(clean_content)
                
                # Validate required fields with defaults
                validated = {
                    "trading_bias": analysis.get("trading_bias", "neutral"),
                    "confidence": float(analysis.get("confidence", 0.5)),
                    "patterns_detected": analysis.get("patterns_detected", []),
                    "support_levels": analysis.get("support_levels", [])[:3],  # Max 3
                    "resistance_levels": analysis.get("resistance_levels", [])[:3],  # Max 3
                    "suggested_entry": analysis.get("suggested_entry"),
                    "suggested_stop": analysis.get("suggested_stop"),
                    "suggested_target": analysis.get("suggested_target"),
                    "key_insights": analysis.get("key_insights", [])[:5],  # Max 5
                    "mode": "ai",
                    "model": OPENROUTER_VISION_MODEL,
                    "configured": True
                }
                
                return validated
                
            except json.JSONDecodeError as e:
                print(f"[AI ERROR] JSON parse failed: {e}", flush=True)
                print(f"[AI ERROR] Raw content: {ai_content[:500]}", flush=True)
                
                # Return raw content formatted nicely
                return {
                    "trading_bias": "neutral",
                    "confidence": 0.5,
                    "patterns_detected": [{"name": "Analysis Completed", "reliability": "medium"}],
                    "support_levels": [],
                    "resistance_levels": [],
                    "suggested_entry": None,
                    "suggested_stop": None,
                    "suggested_target": None,
                    "key_insights": [ai_response[:300] + "..." if len(ai_response) > 300 else ai_response],
                    "mode": "raw",
                    "configured": True
                }
                
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "Chart analysis timed out. Try a smaller image.")
    except Exception as e:
        print(f"[AI ERROR] Chart analysis exception: {e}", flush=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")
