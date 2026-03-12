"""
Pipways AI Services
Supports: CSV, Excel, PDF, and Image analysis
"""

import os
import io
import httpx
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

router = APIRouter()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "anthropic/claude-3.5-sonnet")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are Pipways AI Trading Mentor.

Provide professional trading insights about:

• risk management
• trading psychology
• discipline
• technical analysis

Always emphasize risking only 1–2% per trade.
"""


async def call_openrouter(messages, model):

    if not OPENROUTER_API_KEY:
        raise HTTPException(500, "OpenRouter API key not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2000
    }

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise HTTPException(500, response.text)

        data = response.json()

        return data["choices"][0]["message"]["content"]


# ------------------------------
# AI MENTOR
# ------------------------------

@router.post("/mentor")
async def ai_mentor(data: dict):

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": data.get("message")}
    ]

    response = await call_openrouter(messages, OPENROUTER_MODEL)

    return {"response": response}


# ------------------------------
# CHART ANALYZER
# ------------------------------

@router.post("/analyze-chart")
async def analyze_chart(
    image: UploadFile = File(...),
    pair: str = Form("EURUSD"),
    timeframe: str = Form("1H"),
    context: str = Form("")
):

    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode()

    prompt = f"""
Analyze this {pair} chart on the {timeframe} timeframe.

Return:

Market Bias
Support
Resistance
Trade Setup
Entry
Stop Loss
Take Profit
Probability
"""

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.content_type};base64,{image_b64}"
                }
            }
        ]
    }]

    analysis = await call_openrouter(messages, OPENROUTER_VISION_MODEL)

    return {"analysis": analysis}


# ------------------------------
# PERFORMANCE ANALYZER (MULTI-FORMAT)
# ------------------------------

def is_spreadsheet(filename: str, content_type: str) -> bool:
    """Check if file is CSV or Excel"""
    spreadsheet_types = [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/csv',
        'text/x-csv'
    ]
    return content_type in spreadsheet_types or filename.endswith(('.csv', '.xls', '.xlsx'))

def is_image(content_type: str) -> bool:
    """Check if file is an image"""
    return content_type.startswith('image/')

def is_pdf(content_type: str, filename: str) -> bool:
    """Check if file is PDF"""
    return content_type == 'application/pdf' or filename.endswith('.pdf')


@router.post("/analyze-performance-file")
async def analyze_performance_file(file: UploadFile = File(...)):
    
    filename = file.filename.lower()
    content_type = file.content_type or ""
    file_bytes = await file.read()
    
    try:
        # Path 1: Structured Data (CSV/Excel)
        if is_spreadsheet(filename, content_type):
            return await analyze_structured_data(file_bytes, filename)
        
        # Path 2: Vision Analysis (PDF/Images)
        elif is_image(content_type) or is_pdf(content_type, filename):
            return await analyze_with_vision(file_bytes, content_type, filename)
        
        else:
            raise HTTPException(400, f"Unsupported file type: {content_type}. Please upload CSV, Excel, PDF, or Image.")
            
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


async def analyze_structured_data(file_bytes: bytes, filename: str):
    """Analyze CSV/Excel files using traditional parsing"""
    try:
        # Import here to handle missing dependencies gracefully
        from .services.performance_parser import parse_statement
        from .services.trading_metrics import calculate_metrics
        
        df = parse_statement(file_bytes, filename)
        metrics = calculate_metrics(df)
        
    except ImportError:
        # Fallback if parsers not available
        metrics = {
            "trades": len(str(file_bytes).split('\n')) - 1,
            "win_rate": 0,
            "profit_factor": 0,
            "risk_reward": 0,
            "expectancy": 0,
            "source": "basic_count"
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to parse spreadsheet: {str(e)}")
    
    metrics_text = f"""
Trading Performance Statistics:

Total Trades: {metrics.get('trades', 0)}
Win Rate: {metrics.get('win_rate', 0)}%
Profit Factor: {metrics.get('profit_factor', 0)}
Risk Reward Ratio: {metrics.get('risk_reward', 0)}
Expectancy: {metrics.get('expectancy', 0)}
"""
    
    prompt = f"""
You are a hedge fund trading performance coach.

Analyze the following trading statistics extracted from the user's statement:

{metrics_text}

Provide detailed insights in these sections:

Performance Summary (2-3 sentences overview)
Key Issues (bullet points of major problems)
Strengths (what the trader is doing well)
Improvement Plan (actionable steps)
Recommended Courses (specific course topics)
Mentor Advice (personalized encouragement)
Risk Management Score (0-100)
Discipline Score (0-100)
"""
    
    ai_analysis = await call_openrouter(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        OPENROUTER_MODEL
    )
    
    return {
        "metrics": metrics,
        "analysis": ai_analysis,
        "source": "structured_data"
    }


async def analyze_with_vision(file_bytes: bytes, content_type: str, filename: str):
    """Analyze PDFs and Images using AI Vision OCR"""
    
    # Encode file to base64
    file_b64 = base64.b64encode(file_bytes).decode()
    
    # Determine MIME type for data URI
    if content_type == 'application/pdf':
        # For PDFs, we'll treat them as images if possible, or extract text via vision
        mime_type = "application/pdf"
        file_type_desc = "PDF trading statement"
    else:
        mime_type = content_type
        file_type_desc = "trading statement image"
    
    vision_prompt = f"""
You are analyzing a {file_type_desc} from a trading platform (MT4/MT5/cTrader).

Extract the following information and provide analysis:

1. First, extract all visible trading data (trades, P&L, dates, symbols)
2. Calculate approximate metrics:
   - Total number of trades
   - Win rate percentage
   - Profit factor
   - Average risk/reward
   
3. Then provide a complete trading analysis with these sections:

Performance Summary
Key Issues
Strengths  
Improvement Plan
Recommended Courses
Mentor Advice
Overall Score (0-100)

Be thorough and specific based on what you can see in the document.
"""
    
    # For images, use image_url format. For PDFs, some vision models support them directly
    if mime_type.startswith('image/'):
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{file_b64}"
                    }
                }
            ]
        }]
    else:
        # For PDFs, attempt to process as text extraction or convert approach
        # Many vision models now support PDFs directly via base64
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt + "\n\n[Document uploaded as PDF - analyze the trading data visible in this document]"},
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": f"data:{mime_type};base64,{file_b64}"
                    }
                }
            ]
        }]
    
    analysis_text = await call_openrouter(messages, OPENROUTER_VISION_MODEL)
    
    # Try to extract metrics from the AI response
    metrics = extract_metrics_from_text(analysis_text)
    
    return {
        "metrics": metrics,
        "analysis": analysis_text,
        "source": "vision_ocr"
    }


def extract_metrics_from_text(text: str) -> dict:
    """Extract numerical metrics from AI analysis text"""
    import re
    
    metrics = {
        "trades": 0,
        "win_rate": 0,
        "profit_factor": 0,
        "risk_reward": 0,
        "expectancy": 0,
        "overall_score": 0
    }
    
    # Extract trades
    trade_match = re.search(r'(?:Total\s+)?Trades[:\s]+(\d+)', text, re.IGNORECASE)
    if trade_match:
        metrics["trades"] = int(trade_match.group(1))
    
    # Extract win rate
    win_match = re.search(r'Win\s+Rate[:\s]+(\d+(?:\.\d+)?)\s*%?', text, re.IGNORECASE)
    if win_match:
        metrics["win_rate"] = float(win_match.group(1))
    
    # Extract profit factor
    pf_match = re.search(r'Profit\s+Factor[:\s]+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if pf_match:
        metrics["profit_factor"] = float(pf_match.group(1))
    
    # Extract overall score
    score_match = re.search(r'Overall\s+Score[:\s]+(\d+)', text, re.IGNORECASE)
    if score_match:
        metrics["overall_score"] = int(score_match.group(1))
    
    return metrics
