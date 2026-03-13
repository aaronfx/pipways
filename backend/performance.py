"""
Performance Analyzer - PRODUCTION READY
Supports CSV uploads and JSON data for trading journal analysis
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from typing import List, Optional
from datetime import datetime
import io
import csv
import json
import os
import httpx

from .security import get_current_user

router = APIRouter()

# OpenRouter Configuration (optional - for AI insights)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""

@router.post("/analyze-journal")
async def analyze_trading_journal(
    trades: List[dict],
    current_user = Depends(get_current_user)
):
    """
    Analyze trading journal from JSON data (array of trade objects).
    Frontend sends: [{"symbol": "EURUSD", "direction": "BUY", "pnl": 50, "outcome": "win"}]
    """
    try:
        if not trades or len(trades) == 0:
            raise HTTPException(400, "No trades provided")
        
        # Calculate performance metrics
        analysis = calculate_performance_metrics(trades)
        
        # Add AI insights if OpenRouter configured
        if OPENROUTER_CONFIGURED:
            try:
                ai_insights = await get_ai_insights(analysis)
                analysis["ai_insights"] = ai_insights
            except:
                pass
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PERFORMANCE ERROR] {e}", flush=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.post("/analyze-journal-upload")
async def analyze_journal_upload(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Analyze uploaded trading journal file (CSV, Excel, etc).
    Frontend calls this when user drops a file.
    """
    try:
        if not file:
            raise HTTPException(400, "No file uploaded")
        
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(400, "Empty file")
        
        if len(contents) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(413, "File too large. Max 5MB.")
        
        filename = file.filename.lower()
        content_type = file.content_type or ""
        
        # Parse based on file type
        if 'csv' in content_type or filename.endswith('.csv'):
            trades = parse_csv(contents)
        elif 'json' in content_type or filename.endswith('.json'):
            trades = json.loads(contents.decode('utf-8'))
        elif 'excel' in content_type or filename.endswith(('.xls', '.xlsx')):
            raise HTTPException(501, "Excel support coming soon. Please use CSV or JSON.")
        elif 'pdf' in content_type or filename.endswith('.pdf'):
            raise HTTPException(501, "PDF parsing coming soon.")
        else:
            # Try CSV as default
            try:
                trades = parse_csv(contents)
            except:
                raise HTTPException(400, "Unsupported file format. Please use CSV or JSON.")
        
        if not trades or len(trades) == 0:
            raise HTTPException(400, "No trades found in file.")
        
        # Calculate metrics
        analysis = calculate_performance_metrics(trades)
        analysis["filename"] = file.filename
        analysis["mode"] = "file_upload"
        
        return analysis
        
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON format")
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}", flush=True)
        raise HTTPException(500, f"Upload failed: {str(e)}")

def parse_csv(content: bytes) -> List[dict]:
    """Parse CSV trading statement into trade objects"""
    try:
        text = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        trades = []
        
        for row in reader:
            # Normalize various CSV column names
            trade = {
                "symbol": row.get("Symbol") or row.get("symbol") or row.get("Pair") or "UNKNOWN",
                "direction": row.get("Direction") or row.get("direction") or row.get("Type") or row.get("Side") or "BUY",
                "entry_price": parse_float(row.get("EntryPrice") or row.get("entry_price") or row.get("Open") or 0),
                "exit_price": parse_float(row.get("ExitPrice") or row.get("exit_price") or row.get("Close") or 0),
                "pnl": parse_float(row.get("Profit") or row.get("pnl") or row.get("P&L") or row.get("Gain") or 0),
                "outcome": determine_outcome(row),
                "entry_date": row.get("Date") or row.get("entry_date") or row.get("Time") or datetime.now().isoformat()
            }
            trades.append(trade)
        
        return trades
        
    except Exception as e:
        raise ValueError(f"CSV parsing failed: {str(e)}")

def parse_float(value) -> float:
    """Safely parse float from string"""
    if value is None or value == "":
        return 0.0
    try:
        return float(str(value).replace(',', ''))
    except:
        return 0.0

def determine_outcome(row: dict) -> str:
    """Determine win/loss/breakeven from row data"""
    pnl = parse_float(row.get("Profit") or row.get("pnl") or row.get("P&L") or row.get("Gain") or 0)
    if pnl > 0:
        return "win"
    elif pnl < 0:
        return "loss"
    return "breakeven"

def calculate_performance_metrics(trades: List[dict]) -> dict:
    """Calculate comprehensive trading performance metrics"""
    total = len(trades)
    if total == 0:
        return {"error": "No trades to analyze"}
    
    # Separate wins and losses
    wins = [t for t in trades if t.get("outcome") == "win" or t.get("pnl", 0) > 0]
    losses = [t for t in trades if t.get("outcome") == "loss" or t.get("pnl", 0) < 0]
    breakeven = [t for t in trades if t.get("pnl", 0) == 0]
    
    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(breakeven)
    
    # Core metrics
    win_rate = (win_count / total * 100) if total > 0 else 0
    
    gross_profit = sum(t.get("pnl", 0) for t in wins)
    gross_loss = abs(sum(t.get("pnl", 0) for t in losses))
    net_pnl = gross_profit - gross_loss
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0)
    
    # Expectancy calculation
    avg_win = gross_profit / win_count if win_count > 0 else 0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0
    expectancy = ((win_rate / 100) * avg_win) - ((1 - win_rate / 100) * avg_loss)
    
    # Grade
    grade = calculate_grade(win_rate, profit_factor)
    
    # Improvement suggestions
    improvements = generate_improvements(win_rate, profit_factor, avg_win, avg_loss, win_count, loss_count)
    
    return {
        "statistics": {
            "total_trades": total,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "breakeven_trades": be_count,
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "∞",
            "expectancy": round(expectancy, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "net_pnl": round(net_pnl, 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
            "largest_win": round(max([t.get("pnl", 0) for t in wins]) if wins else 0, 2),
            "largest_loss": round(min([t.get("pnl", 0) for t in losses]) if losses else 0, 2)
        },
        "overall_grade": grade,
        "improvements": improvements,
        "trades_sample": trades[:5],  # First 5 trades for verification
        "analysis_date": datetime.now().isoformat()
    }

def generate_improvements(win_rate, pf, avg_win, avg_loss, win_count, loss_count):
    """Generate actionable trading improvements based on metrics"""
    suggestions = []
    
    if win_rate < 40:
        suggestions.append("Win rate below 40%. Review your entry criteria and be more selective.")
    elif win_rate < 50:
        suggestions.append("Win rate is below 50%. Focus on high-probability setups.")
    
    if pf < 1.0:
        suggestions.append("Profit factor below 1.0 - you're losing money overall. Stop trading and review strategy.")
    elif pf < 1.5:
        suggestions.append("Profit factor could be improved. Let winners run longer or cut losses quicker.")
    
    if avg_loss > avg_win * 0.8:
        suggestions.append("Losses are too large relative to wins. Tighten stop losses or reduce position size.")
    
    if win_count > 0 and loss_count > 0 and (avg_win / avg_loss if avg_loss > 0 else 0) < 1.5:
        suggestions.append("Risk:Reward ratio needs improvement. Aim for at least 1:2 risk/reward.")
    
    if not suggestions:
        suggestions.append("Excellent performance! Maintain your discipline and consistency.")
        suggestions.append("Consider gradually increasing position size while maintaining risk management.")
    
    return suggestions

def calculate_grade(wr, pf):
    """Calculate letter grade (A-F) based on performance"""
    score = 0
    
    # Win rate scoring
    if wr >= 60: score += 35
    elif wr >= 55: score += 30
    elif wr >= 50: score += 25
    elif wr >= 45: score += 20
    elif wr >= 40: score += 15
    
    # Profit factor scoring
    if pf >= 2.5: score += 35
    elif pf >= 2.0: score += 30
    elif pf >= 1.5: score += 25
    elif pf >= 1.0: score += 20
    elif pf > 0: score += 10
    
    # Letter grade
    if score >= 60: return "A"
    if score >= 50: return "B"
    if score >= 40: return "C"
    if score >= 30: return "D"
    return "F"

async def get_ai_insights(analysis: dict) -> str:
    """Get AI-powered insights from OpenRouter (optional)"""
    if not OPENROUTER_CONFIGURED:
        return ""
    
    try:
        stats = analysis["statistics"]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://pipwaysapp.onrender.com",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a trading performance analyst. Provide 2-3 specific, actionable insights about the trading performance data provided. Be concise and encouraging."
                        },
                        {
                            "role": "user",
                            "content": f"Win rate: {stats['win_rate']}%, Profit factor: {stats['profit_factor']}, Net P&L: ${stats['net_pnl']}, Grade: {analysis['overall_grade']}"
                        }
                    ],
                    "max_tokens": 300
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
    except:
        pass
    
    return ""

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """Get performance statistics for dashboard display"""
    try:
        # In production: query database for user's actual stats
        # For now return empty stats
        return {
            "period_days": days,
            "summary": {
                "trades_taken": 0,
                "win_rate": 0,
                "net_pnl": 0,
                "grade": "-"
            },
            "message": "Upload your trading data to see statistics"
        }
    except Exception as e:
        print(f"[STATS ERROR] {e}", flush=True)
        return {
            "period_days": days,
            "summary": {
                "trades_taken": 0,
                "win_rate": 0,
                "net_pnl": 0,
                "grade": "-"
            }
        }
