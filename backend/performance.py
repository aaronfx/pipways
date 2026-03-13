"""Performance Analytics API - PRODUCTION READY"""
import os
import io
import csv
import json
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .security import get_current_user

router = APIRouter()

# Try to import optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

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
    Analyze uploaded trading journal file.
    Supports: CSV, Excel (.xlsx, .xls), PDF, Images (PNG, JPG, JPEG)
    """
    try:
        if not file:
            raise HTTPException(400, "No file uploaded")
        
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(400, "Empty file")
        
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(413, "File too large. Max 10MB.")
        
        filename = file.filename.lower()
        content_type = file.content_type or ""
        
        trades = []
        
        # Parse based on file type
        if 'csv' in content_type or filename.endswith('.csv'):
            trades = parse_csv(contents)
            
        elif any(ext in filename for ext in ['.xlsx', '.xls']) or 'excel' in content_type or 'spreadsheet' in content_type:
            if not PANDAS_AVAILABLE:
                raise HTTPException(501, "Excel support not available. Install pandas: pip install pandas openpyxl")
            trades = parse_excel(contents, filename)
            
        elif 'pdf' in content_type or filename.endswith('.pdf'):
            if not PDF_AVAILABLE:
                raise HTTPException(501, "PDF support not available. Install PyPDF2: pip install PyPDF2")
            trades = parse_pdf(contents)
            
        elif 'image' in content_type or any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif']):
            if not OCR_AVAILABLE:
                raise HTTPException(501, "Image OCR not available. Install pytesseract: pip install pytesseract Pillow")
            trades = parse_image(contents, filename)
            
        elif 'json' in content_type or filename.endswith('.json'):
            data = json.loads(contents.decode('utf-8'))
            if isinstance(data, list):
                trades = data
            elif isinstance(data, dict) and 'trades' in data:
                trades = data['trades']
            else:
                raise HTTPException(400, "Invalid JSON format. Expected array of trades or {trades: [...]}")
        else:
            # Try CSV as default
            try:
                trades = parse_csv(contents)
            except:
                raise HTTPException(400, "Unsupported file format. Please use CSV, Excel, PDF, Image, or JSON.")
        
        if not trades or len(trades) == 0:
            raise HTTPException(400, "No trades found in file.")
        
        analysis = calculate_performance_metrics(trades)
        analysis["filename"] = file.filename
        analysis["mode"] = "file_upload"
        analysis["file_type"] = content_type or "unknown"
        
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
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                text = content.decode(encoding)
                break
            except:
                continue
        else:
            text = content.decode('utf-8', errors='ignore')
        
        # Try to detect delimiter
        sample = text[:2000]
        delimiter = ','
        if '\t' in sample and sample.count('\t') > sample.count(','):
            delimiter = '\t'
        elif ';' in sample and sample.count(';') > sample.count(','):
            delimiter = ';'
        
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        trades = []
        
        for row in reader:
            if not any(row.values()):  # Skip empty rows
                continue
                
            trade = {
                "symbol": row.get("Symbol") or row.get("symbol") or row.get("Pair") or row.get("pair") or "UNKNOWN",
                "direction": row.get("Direction") or row.get("direction") or row.get("Type") or row.get("Side") or row.get("Action") or "BUY",
                "entry_price": parse_float(row.get("EntryPrice") or row.get("entry_price") or row.get("Open") or row.get("Open Price") or 0),
                "exit_price": parse_float(row.get("ExitPrice") or row.get("exit_price") or row.get("Close") or row.get("Close Price") or 0),
                "pnl": parse_float(row.get("Profit") or row.get("pnl") or row.get("P&L") or row.get("Gain") or row.get("Profit/Loss") or 0),
                "outcome": determine_outcome(row),
                "entry_date": row.get("Date") or row.get("entry_date") or row.get("Time") or row.get("Open Time") or datetime.now().isoformat()
            }
            trades.append(trade)
        
        if not trades:
            raise ValueError("No valid trade data found in CSV")
            
        return trades
        
    except Exception as e:
        raise ValueError(f"CSV parsing failed: {str(e)}")

def parse_excel(content: bytes, filename: str) -> List[dict]:
    """Parse Excel trading statement"""
    try:
        import pandas as pd
        
        # Read Excel file
        df = pd.read_excel(io.BytesIO(content))
        
        # Convert to list of dicts
        trades = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            if not any(row_dict.values()):  # Skip empty rows
                continue
                
            trade = {
                "symbol": str(row_dict.get("Symbol", row_dict.get("symbol", row_dict.get("Pair", "UNKNOWN")))),
                "direction": str(row_dict.get("Direction", row_dict.get("direction", row_dict.get("Type", "BUY")))),
                "entry_price": parse_float(row_dict.get("EntryPrice", row_dict.get("entry_price", row_dict.get("Open", 0)))),
                "exit_price": parse_float(row_dict.get("ExitPrice", row_dict.get("exit_price", row_dict.get("Close", 0)))),
                "pnl": parse_float(row_dict.get("Profit", row_dict.get("pnl", row_dict.get("P&L", row_dict.get("Gain", 0)))),
                "outcome": determine_outcome_from_pnl(parse_float(row_dict.get("Profit", row_dict.get("pnl", row_dict.get("P&L", 0))))),
                "entry_date": str(row_dict.get("Date", row_dict.get("entry_date", row_dict.get("Time", datetime.now().isoformat()))))
            }
            trades.append(trade)
        
        return trades
        
    except Exception as e:
        raise ValueError(f"Excel parsing failed: {str(e)}")

def parse_pdf(content: bytes) -> List[dict]:
    """Parse PDF trading statement"""
    try:
        import PyPDF2
        import re
        
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # Try to extract trades using regex patterns
        trades = []
        
        # Common patterns for trading statements
        patterns = [
            # Pattern: Symbol Direction Entry Exit P/L
            r'([A-Z]{3,6})[/\s]?([A-Z]{3,6})?\s+(BUY|SELL|Long|Short)\s+[\d\.]+\s+[\d\.]+\s+([-\d\.]+)',
            # Pattern: Date Symbol Type Profit
            r'(\d{4}[-/]\d{2}[-/]\d{2}).*?([A-Z]{3,6})[/\s]?([A-Z]{3,6})?.*?(BUY|SELL).*?([-\d\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    if len(groups) >= 4:
                        symbol = (groups[0] or "") + (groups[1] or "")
                        direction = groups[2] if groups[2] in ['BUY', 'SELL', 'Long', 'Short'] else 'BUY'
                        pnl = parse_float(groups[-1])
                        
                        trades.append({
                            "symbol": symbol or "UNKNOWN",
                            "direction": direction,
                            "entry_price": 0,
                            "exit_price": 0,
                            "pnl": pnl,
                            "outcome": "win" if pnl > 0 else "loss" if pnl < 0 else "breakeven",
                            "entry_date": datetime.now().isoformat()
                        })
                except:
                    continue
        
        # If no trades found with patterns, try line-by-line parsing
        if not trades:
            lines = text.split('\n')
            for line in lines:
                # Look for currency pairs and numbers
                if re.search(r'(EUR|GBP|USD|JPY|AUD|CAD|CHF|NZD|XAU|XAG)', line):
                    numbers = re.findall(r'[-+]?\d+\.?\d*', line)
                    if len(numbers) >= 1:
                        # Assume last number is P&L
                        pnl = parse_float(numbers[-1])
                        symbol_match = re.search(r'([A-Z]{3,6})[/]?(?:[A-Z]{3,6})?', line)
                        symbol = symbol_match.group(1) if symbol_match else "UNKNOWN"
                        
                        trades.append({
                            "symbol": symbol,
                            "direction": "BUY" if "Buy" in line or "buy" in line else "SELL",
                            "entry_price": 0,
                            "exit_price": 0,
                            "pnl": pnl,
                            "outcome": "win" if pnl > 0 else "loss" if pnl < 0 else "breakeven",
                            "entry_date": datetime.now().isoformat()
                        })
        
        if not trades:
            raise ValueError("Could not extract trade data from PDF. Please use CSV or Excel format.")
            
        return trades
        
    except Exception as e:
        raise ValueError(f"PDF parsing failed: {str(e)}")

def parse_image(content: bytes, filename: str) -> List[dict]:
    """Parse image using OCR for trading statement screenshots"""
    try:
        from PIL import Image
        import pytesseract
        import re
        
        image = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(image)
        
        # Similar to PDF parsing - extract trades from OCR text
        trades = []
        
        # Look for tabular data patterns
        lines = text.split('\n')
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Look for patterns like: SYMBOL Direction P/L
            # Example: EURUSD BUY +50.00 or GBPUSD SELL -25.00
            pattern = r'([A-Z]{3,6})[/]?(?:[A-Z]{3,6})?\s+(BUY|SELL|Long|Short)?\s*([+-]?\d+\.?\d*)'
            match = re.search(pattern, line, re.IGNORECASE)
            
            if match:
                symbol = match.group(1)
                direction = match.group(2) or "BUY"
                pnl = parse_float(match.group(3))
                
                if symbol and pnl != 0:  # Only add if we found valid data
                    trades.append({
                        "symbol": symbol,
                        "direction": direction.upper() if direction else "BUY",
                        "entry_price": 0,
                        "exit_price": 0,
                        "pnl": pnl,
                        "outcome": "win" if pnl > 0 else "loss" if pnl < 0 else "breakeven",
                        "entry_date": datetime.now().isoformat()
                    })
        
        if not trades:
            raise ValueError("Could not extract trade data from image. Please ensure the image clearly shows your trading data with symbols and P&L values.")
            
        return trades
        
    except Exception as e:
        raise ValueError(f"Image OCR failed: {str(e)}")

def parse_float(value) -> float:
    """Safely parse float"""
    if value is None or value == "":
        return 0.0
    try:
        # Remove currency symbols and commas
        if isinstance(value, str):
            value = value.replace('$', '').replace('€', '').replace('£', '').replace(',', '').strip()
        return float(value)
    except:
        return 0.0

def determine_outcome(row: dict) -> str:
    """Determine win/loss"""
    pnl = parse_float(row.get("Profit") or row.get("pnl") or row.get("P&L") or row.get("Gain") or 0)
    return determine_outcome_from_pnl(pnl)

def determine_outcome_from_pnl(pnl: float) -> str:
    """Determine outcome from P&L value"""
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
            "average_loss": round(avg_loss, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2)
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
