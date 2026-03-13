"""Performance Analytics API - PRODUCTION READY"""
import os
import io
import csv
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .security import get_current_user

router = APIRouter()

# Pydantic models for request validation
class TradeData(BaseModel):
    symbol: str
    direction: str
    entry_price: Optional[float] = 0
    exit_price: Optional[float] = 0
    pnl: float
    outcome: str

class JournalRequest(BaseModel):
    trades: List[dict]

@router.post("/analyze-journal")
async def analyze_journal(
    request: JournalRequest,
    current_user = Depends(get_current_user)
):
    """
    Analyze trading journal from JSON data.
    Request body: {"trades": [{"symbol": "EURUSD", "pnl": 50, "outcome": "win"}]}
    """
    try:
        if not request.trades or len(request.trades) == 0:
            raise HTTPException(400, "No trades provided")
        
        analysis = calculate_performance_metrics(request.trades)
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
    Analyze uploaded trading journal file (CSV).
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
        
        # Parse CSV
        if 'csv' in content_type or filename.endswith('.csv'):
            trades = parse_csv(contents)
        elif 'json' in content_type or filename.endswith('.json'):
            trades = json.loads(contents.decode('utf-8'))
        else:
            raise HTTPException(400, "Unsupported format. Use CSV or JSON.")
        
        if not trades or len(trades) == 0:
            raise HTTPException(400, "No trades found in file.")
        
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
    """Parse CSV trading statement"""
    try:
        text = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(text))
        trades = []
        
        for row in reader:
            trade = {
                "symbol": row.get("Symbol") or row.get("symbol") or "UNKNOWN",
                "direction": row.get("Direction") or row.get("direction") or "BUY",
                "entry_price": parse_float(row.get("EntryPrice") or row.get("entry_price") or 0),
                "exit_price": parse_float(row.get("ExitPrice") or row.get("exit_price") or 0),
                "pnl": parse_float(row.get("Profit") or row.get("pnl") or row.get("P&L") or 0),
                "outcome": determine_outcome(row),
                "entry_date": row.get("Date") or row.get("entry_date") or datetime.now().isoformat()
            }
            trades.append(trade)
        
        return trades
        
    except Exception as e:
        raise ValueError(f"CSV parsing failed: {str(e)}")

def parse_float(value) -> float:
    """Safely parse float"""
    if value is None or value == "":
        return 0.0
    try:
        return float(str(value).replace(',', ''))
    except:
        return 0.0

def determine_outcome(row: dict) -> str:
    """Determine win/loss"""
    pnl = parse_float(row.get("Profit") or row.get("pnl") or row.get("P&L") or 0)
    if pnl > 0:
        return "win"
    elif pnl < 0:
        return "loss"
    return "breakeven"

def calculate_performance_metrics(trades: List[dict]) -> dict:
    """Calculate comprehensive performance metrics"""
    total = len(trades)
    if total == 0:
        return {"error": "No trades to analyze"}
    
    wins = [t for t in trades if t.get("outcome") == "win" or t.get("pnl", 0) > 0]
    losses = [t for t in trades if t.get("outcome") == "loss" or t.get("pnl", 0) < 0]
    
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total * 100) if total > 0 else 0
    
    gross_profit = sum(t.get("pnl", 0) for t in wins)
    gross_loss = abs(sum(t.get("pnl", 0) for t in losses))
    net_pnl = gross_profit - gross_loss
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    avg_win = gross_profit / win_count if win_count > 0 else 0
    avg_loss = gross_loss / loss_count if loss_count > 0 else 0
    expectancy = ((win_rate / 100) * avg_win) - ((1 - win_rate / 100) * abs(avg_loss))
    
    # Grade
    grade = "F"
    if win_rate >= 60 and profit_factor >= 2:
        grade = "A"
    elif win_rate >= 55 and profit_factor >= 1.5:
        grade = "B"
    elif win_rate >= 50 and profit_factor >= 1.0:
        grade = "C"
    elif win_rate >= 40:
        grade = "D"
    
    # Suggestions
    improvements = []
    if win_rate < 50:
        improvements.append("Win rate below 50%. Review entry criteria.")
    if profit_factor < 1.5:
        improvements.append("Profit factor could be improved. Let winners run longer.")
    if avg_loss > avg_win * 0.8:
        improvements.append("Losses too large relative to wins. Tighten stops.")
    if not improvements:
        improvements.append("Good performance! Maintain consistency.")
    
    return {
        "statistics": {
            "total_trades": total,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "expectancy": round(expectancy, 2),
            "net_pnl": round(net_pnl, 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2)
        },
        "overall_grade": grade,
        "improvements": improvements,
        "trades_sample": trades[:5]
    }

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """Get performance statistics"""
    return {
        "period_days": days,
        "summary": {
            "trades_taken": 0,
            "win_rate": 0,
            "net_pnl": 0,
            "grade": "-"
        },
        "message": "Upload trading data to see statistics"
    }
