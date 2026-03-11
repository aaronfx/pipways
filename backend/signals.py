"""
Signals Routes
Handles trading signals display and management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List

from . import database
from .security import get_current_user_optional, get_admin_user

router = APIRouter()

@router.get("")
async def get_signals(pair: Optional[str] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get all active signals"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        if pair:
            signals = await conn.fetch("SELECT * FROM signals WHERE pair = $1 AND status = 'active' ORDER BY created_at DESC", pair)
        else:
            signals = await conn.fetch("SELECT * FROM signals WHERE status = 'active' ORDER BY created_at DESC")
        
        # FIXED: Return wrapped response
        return {"signals": [dict(s) for s in signals]}

@router.get("/history")
async def get_signal_history(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get historical signals"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        signals = await conn.fetch("SELECT * FROM signals WHERE status != 'active' ORDER BY closed_at DESC LIMIT 50")
        return {"signals": [dict(s) for s in signals]}
