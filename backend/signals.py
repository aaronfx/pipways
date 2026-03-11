"""
Signals Routes
Handles trading signals display and management
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from . import database
from .security import get_current_user_optional, get_admin_user
from .schemas import SignalCreate

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
        
        # Return wrapped response
        return {"signals": [dict(s) for s in signals]}

@router.get("/history")
async def get_signal_history(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get historical signals"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        signals = await conn.fetch("SELECT * FROM signals WHERE status != 'active' ORDER BY closed_at DESC LIMIT 50")
        return {"signals": [dict(s) for s in signals]}

@router.get("/{signal_id}")
async def get_signal(signal_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single signal by ID"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        signal = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        return dict(signal)

@router.post("")
async def create_signal(signal: SignalCreate, current_user: dict = Depends(get_admin_user)):
    """Create new signal (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (pair, direction, entry_price, stop_loss, tp1, tp2, analysis, is_premium, created_by, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING id
        """, signal.pair, signal.direction, signal.entry_price, 
            signal.stop_loss, signal.tp1, signal.tp2, signal.analysis, 
            signal.is_premium, current_user['id'], signal.status)
        
        return {"id": signal_id, "message": "Signal created successfully"}

@router.put("/{signal_id}")
async def update_signal(signal_id: int, signal: SignalCreate, current_user: dict = Depends(get_admin_user)):
    """Update signal (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE signals 
            SET pair = $1, direction = $2, entry_price = $3, stop_loss = $4, 
                tp1 = $5, tp2 = $6, analysis = $7, is_premium = $8, status = $9, updated_at = CURRENT_TIMESTAMP
            WHERE id = $10
        """, signal.pair, signal.direction, signal.entry_price, signal.stop_loss,
            signal.tp1, signal.tp2, signal.analysis, signal.is_premium, signal.status, signal_id)
        
        return {"message": "Signal updated successfully"}

@router.delete("/{signal_id}")
async def delete_signal(signal_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete signal (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        return {"message": "Signal deleted successfully"}
