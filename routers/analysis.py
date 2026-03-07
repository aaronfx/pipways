from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from typing import Optional
import base64
import json
import uuid
from datetime import datetime
from pathlib import Path

from auth import get_current_user
from database import get_db
from config import settings, ALLOWED_TRADE_FILE_TYPES
from services.openrouter import openrouter_vision
from services.file_processor import (
    extract_text_from_pdf, 
    extract_text_from_docx, 
    parse_csv_trades, 
    parse_mt4_statement
)
from services.analyzer import analyze_trader_performance, parse_chart_analysis

router = APIRouter()

# Ensure upload directories exist
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)
MEDIA_DIR = UPLOAD_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

@router.post("/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Analyze chart image with AI"""
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')

        analysis_text, error = openrouter_vision(
            base64_image,
            "Analyze this trading chart. Identify the currency pair, trend direction, key support/resistance levels, and provide a trade setup grade (A/B/C)."
        )

        if error:
            return {
                "success": False,
                "error": error,
                "image_data": base64_image
            }

        parsed = parse_chart_analysis(analysis_text)

        # Save to database
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        await conn.execute(
            "INSERT INTO chart_analyses (user_id, image_data, analysis_result) VALUES ($1, $2, $3)",
            user["id"], base64_image, json.dumps(parsed)
        )

        return {
            "success": True,
            "analysis": parsed,
            "image_data": base64_image
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/chart/history")
async def get_chart_analyses(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get chart analysis history"""
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        analyses = await conn.fetch(
            "SELECT id, analysis_result, created_at FROM chart_analyses WHERE user_id = $1 ORDER BY created_at DESC",
            user["id"]
        )
        return [dict(a) for a in analyses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trade-file")
async def analyze_trade_file(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Upload and analyze trading statement (PDF, CSV, etc.)"""
    try:
        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")

        # Detect file type
        file_type = file.content_type or "application/octet-stream"
        ext = Path(file.filename).suffix.lower()

        # Extract data based on file type
        extracted_data = {}

        if file_type == 'application/pdf':
            extracted_data['text'] = extract_text_from_pdf(contents)
            extracted_data['type'] = 'pdf_statement'
        elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            extracted_data['text'] = extract_text_from_docx(contents)
            extracted_data['type'] = 'doc_report'
        elif file_type == 'text/csv':
            extracted_data['trades'] = parse_csv_trades(contents)
            extracted_data['type'] = 'csv_trades'
        elif file_type in ['image/png', 'image/jpeg', 'image/webp']:
            base64_image = base64.b64encode(contents).decode('utf-8')
            extracted_data['image_data'] = base64_image
            extracted_data['type'] = 'screenshot'
        elif 'mt4' in file.filename.lower() or 'mt5' in file.filename.lower():
            extracted_data = parse_mt4_statement(contents)
            extracted_data['type'] = 'mt_statement'

        # Save file
        file_ext = ALLOWED_TRADE_FILE_TYPES.get(file_type, '.bin')
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = MEDIA_DIR / unique_filename

        with open(file_path, "wb") as f:
            f.write(contents)

        # AI analysis
        analysis = await analyze_trader_performance(extracted_data, 0)

        if not analysis.get('success'):
            return {
                "success": False,
                "error": analysis.get('error', 'Analysis failed'),
                "extracted_preview": str(extracted_data)[:500]
            }

        # Save to database
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

        upload_id = await conn.fetchval("""
            INSERT INTO trade_analysis_uploads 
            (user_id, filename, file_type, file_data, extracted_data, analysis_result,
             trader_type, trader_score, mistakes_detected, patterns_detected, 
             recommendations, learning_resources)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
        """,
            user["id"],
            file.filename,
            file_type,
            str(file_path),
            json.dumps(extracted_data),
            json.dumps(analysis),
            analysis.get('trader_type'),
            analysis.get('trader_score'),
            json.dumps(analysis.get('mistakes_detected', [])),
            json.dumps(analysis.get('patterns_detected', [])),
            analysis.get('recommendations', []),
            analysis.get('learning_resources', [])
        )

        return {
            "success": True,
            "upload_id": upload_id,
            "analysis": analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")

@router.get("/trade-file/history")
async def get_trade_analyses(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get trade analysis history"""
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        analyses = await conn.fetch("""
            SELECT id, filename, file_type, trader_type, trader_score, 
                   recommendations, created_at
            FROM trade_analysis_uploads 
            WHERE user_id = $1 
            ORDER BY created_at DESC
        """, user["id"])
        return [dict(a) for a in analyses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
