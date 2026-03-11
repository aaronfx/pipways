"""
Performance Analysis Routes
Handles trading performance analysis and reporting
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from . import database
from .security import get_current_user, get_current_user_optional
from .schemas import PerformanceAnalysisRequest

router = APIRouter()

@router.post("/analyze-vision")
async def analyze_performance_vision(
    data: PerformanceAnalysisRequest, 
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Analyze trading performance from uploaded statement image
    """
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Mock analysis - replace with actual AI integration (OpenAI Vision API, etc.)
    analysis_result = {
        "trader_score": 75,
        "total_trades": 45,
        "win_rate": 62.5,
        "profit_factor": 1.8,
        "average_return": 2.3,
        "top_mistakes": [
            "Holding losing trades too long",
            "Not using stop losses consistently",
            "Overtrading during volatile sessions"
        ],
        "strengths": [
            "Good risk management on winning trades",
            "Consistent position sizing",
            "Profitable trading system overall"
        ],
        "improvement_plan": [
            "Set strict stop loss rules",
            "Limit trades to 3 per day",
            "Review losing trades weekly"
        ],
        "mentor_advice": "Focus on cutting losses quickly. Your win rate is good but letting losers run is hurting your profit factor.",
        "recommended_courses": ["Risk Management Masterclass", "Trading Psychology"]
    }
    
    # Save to database if user is logged in
    if current_user:
        async with database.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO performance_analyses (user_id, analysis_data, trader_score)
                VALUES ($1, $2, $3)
            """, current_user['id'], analysis_result, analysis_result['trader_score'])
    
    return analysis_result
