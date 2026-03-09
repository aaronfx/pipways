
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from typing import Optional
from datetime import datetime
from app.dependencies import get_current_user
from app.models.schemas import PerformanceAnalysisRequest, ChatMessage
from app.services.ai_service import ai_service
from app.config import settings
import asyncpg

router = APIRouter(prefix="/ai", tags=["ai"])

async def get_db():
    return await asyncpg.create_pool(settings.DATABASE_URL)

@router.post("/chat")
async def ai_chat(
    chat: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        response = await ai_service.chat(chat.message, chat.context)

        # Save to history
        pool = await get_db()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_history (user_id, message, response, context, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """, int(current_user["id"]), chat.message, response, chat.context, datetime.utcnow())

        return {"response": response, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history")
async def get_chat_history(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT message, response, context, created_at 
            FROM chat_history 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, int(current_user["id"]), limit)

        return {"history": [dict(row) for row in rows]}

@router.post("/analyze/performance")
async def analyze_performance(
    request: PerformanceAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        analysis = await ai_service.analyze_performance(
            request.trades, 
            request.account_balance
        )
        return {"analysis": analysis, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/chart")
async def analyze_chart(
    file: UploadFile = File(...),
    pair: str = Form("EURUSD"),
    timeframe: str = Form("1H"),
    additional_info: str = Form(""),
    current_user: dict = Depends(get_current_user)
):
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large")

        result = await ai_service.analyze_chart(contents, pair, timeframe, additional_info)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
