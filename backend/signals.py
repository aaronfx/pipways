"""
Enhanced Signals Routes
Added: timeframe, risk/reward calculation, TP1/TP2 hit tracking
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from . import database
from .security import get_current_user_optional, get_admin_user
from .schemas import SignalCreate

router = APIRouter()

def calculate_risk_reward(entry: float, sl: float, tp: float) -> str:
    """Calculate risk to reward ratio"""
    if not entry or not sl or not tp:
        return "N/A"
    try:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk == 0:
            return "N/A"
        ratio = reward / risk
        return f"1:{ratio:.1f}"
    except:
        return "N/A"

@router.get("")
async def get_signals(
    pair: Optional[str] = None, 
    status: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get signals with enhanced filtering"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = "SELECT * FROM signals WHERE 1=1"
        params = []
        
        if pair:
            query += f" AND pair = ${len(params)+1}"
            params.append(pair.upper())
        
        if status:
            query += f" AND status = ${len(params)+1}"
            params.append(status)
        else:
            query += " AND status IN ('active', 'tp1_hit', 'tp2_hit')"
        
        query += " ORDER BY created_at DESC"
        
        signals = await conn.fetch(query, *params)
        return {"signals": [dict(s) for s in signals]}

@router.get("/history")
async def get_signal_history(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get historical closed signals"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        signals = await conn.fetch(
            "SELECT * FROM signals WHERE status IN ('closed', 'sl_hit', 'expired') ORDER BY closed_at DESC NULLS LAST LIMIT 50"
        )
        return {"signals": [dict(s) for s in signals]}

@router.get("/{signal_id}")
async def get_signal(signal_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single signal"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        signal = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        return dict(signal)

@router.post("")
async def create_signal(signal: SignalCreate, current_user: dict = Depends(get_admin_user)):
    """Create new signal with auto-calculated risk/reward"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Calculate risk/reward
    risk_reward = calculate_risk_reward(
        signal.entry_price, 
        signal.stop_loss, 
        signal.tp1
    )
    
    async with database.db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (
                pair, direction, entry_price, stop_loss, tp1, tp2, 
                timeframe, risk_reward_ratio, analysis, is_premium, 
                created_by, status, timeframe
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13) 
            RETURNING id
        """, 
            signal.pair.upper(), 
            signal.direction.lower(), 
            signal.entry_price,
            signal.stop_loss, 
            signal.tp1, 
            signal.tp2, 
            signal.timeframe,
            risk_reward,
            signal.analysis, 
            signal.is_premium, 
            current_user['id'],
            signal.status,
            signal.timeframe
        )
        
        return {
            "id": signal_id, 
            "message": "Signal created successfully",
            "risk_reward_ratio": risk_reward
        }

@router.put("/{signal_id}")
async def update_signal(signal_id: int, signal: SignalCreate, current_user: dict = Depends(get_admin_user)):
    """Update signal"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    risk_reward = calculate_risk_reward(
        signal.entry_price, 
        signal.stop_loss, 
        signal.tp1
    )
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE signals 
            SET pair = $1, direction = $2, entry_price = $3, stop_loss = $4, 
                tp1 = $5, tp2 = $6, timeframe = $7, risk_reward_ratio = $8,
                analysis = $9, is_premium = $10, status = $11, updated_at = CURRENT_TIMESTAMP
            WHERE id = $12
        """, 
            signal.pair.upper(), 
            signal.direction.lower(), 
            signal.entry_price, 
            signal.stop_loss,
            signal.tp1, 
            signal.tp2, 
            signal.timeframe,
            risk_reward,
            signal.analysis, 
            signal.is_premium, 
            signal.status, 
            signal_id
        )
        
        return {
            "message": "Signal updated successfully",
            "risk_reward_ratio": risk_reward
        }

@router.put("/{signal_id}/status")
async def update_signal_status(
    signal_id: int, 
    status: str,  # 'active', 'tp1_hit', 'tp2_hit', 'sl_hit', 'closed'
    current_user: dict = Depends(get_admin_user)
):
    """Update signal status (TP1 hit, TP2 hit, etc.)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    valid_statuses = ['active', 'tp1_hit', 'tp2_hit', 'sl_hit', 'closed', 'expired']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    async with database.db_pool.acquire() as conn:
        # Set flags based on status
        tp1_hit = status == 'tp1_hit' or status == 'tp2_hit'
        tp2_hit = status == 'tp2_hit'
        sl_hit = status == 'sl_hit'
        
        await conn.execute("""
            UPDATE signals 
            SET status = $1, tp1_hit = $2, tp2_hit = $3, sl_hit = $4, 
                closed_at = CASE WHEN $1 IN ('closed', 'sl_hit', 'expired') THEN CURRENT_TIMESTAMP ELSE closed_at END
            WHERE id = $5
        """, status, tp1_hit, tp2_hit, sl_hit, signal_id)
        
        return {"message": f"Signal status updated to {status}"}

@router.delete("/{signal_id}")
async def delete_signal(signal_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete signal"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        return {"message": "Signal deleted successfully"}
