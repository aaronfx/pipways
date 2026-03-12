"""
Signal Routes - Trading Signal System
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging

# ABSOLUTE IMPORTS (no dots)
import database
from schemas import SignalCreate, SignalUpdate, SignalResponse, SignalListResponse
from security import get_current_user, get_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()

def calculate_risk_reward(entry: Decimal, sl: Decimal, tp1: Decimal, direction: str) -> Optional[str]:
    """Calculate Risk/Reward ratio"""
    if not all([entry, sl, tp1]):
        return None
    try:
        if direction == 'buy':
            risk = entry - sl
            reward = tp1 - entry
        else:
            risk = sl - entry
            reward = entry - tp1
        if risk == 0:
            return None
        ratio = reward / risk
        return f"1:{ratio:.2f}"
    except:
        return None

@router.get("/", response_model=List[SignalResponse])
async def get_signals(
    status: Optional[str] = None,
    pair: Optional[str] = None,
    direction: Optional[str] = None,
    current_user: Optional[dict] = Depends(lambda: None)
):
    """Get trading signals with optional filtering"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            SELECT s.*, u.full_name as author_name 
            FROM signals s
            LEFT JOIN users u ON s.created_by = u.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += f" AND s.status = ${len(params)+1}"
            params.append(status)
        if pair:
            query += f" AND s.pair ILIKE ${len(params)+1}"
            params.append(f"%{pair}%")
        if direction:
            query += f" AND s.direction = ${len(params)+1}"
            params.append(direction)
        
        # Hide draft signals from non-admins
        if not current_user or current_user.get('role') not in ['admin', 'moderator']:
            query += " AND s.status != 'draft'"
        
        query += " ORDER BY s.created_at DESC"
        
        signals = await conn.fetch(query, *params)
        return [dict(s) for s in signals]

@router.get("/active")
async def get_active_signals():
    """Get currently active signals"""
    return await get_signals(status="active")

@router.get("/{signal_id}")
async def get_signal(signal_id: int):
    """Get single signal details"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        signal = await conn.fetchrow("""
            SELECT s.*, u.full_name as author_name 
            FROM signals s
            LEFT JOIN users u ON s.created_by = u.id
            WHERE s.id = $1
        """, signal_id)
        
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return dict(signal)

@router.post("/", response_model=SignalResponse)
async def create_signal(
    signal: SignalCreate, 
    current_user: dict = Depends(get_admin_user)
):
    """Create new trading signal (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Calculate risk/reward
    rr_ratio = calculate_risk_reward(
        signal.entry_price, 
        signal.stop_loss, 
        signal.take_profit_1, 
        signal.direction
    )
    
    async with database.db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (
                pair, direction, entry_price, stop_loss, 
                take_profit_1, take_profit_2, take_profit_3,
                risk_reward_ratio, analysis, status, created_by, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, CURRENT_TIMESTAMP)
            RETURNING id
        """,
            signal.pair,
            signal.direction,
            signal.entry_price,
            signal.stop_loss,
            signal.take_profit_1,
            signal.take_profit_2,
            signal.take_profit_3,
            rr_ratio,
            signal.analysis,
            signal.status or 'active',
            current_user['id']
        )
        
        # Log activity
        await database.log_activity(
            user_id=current_user['id'],
            action='create_signal',
            entity_type='signal',
            entity_id=signal_id,
            new_values={"pair": signal.pair, "direction": signal.direction}
        )
        
        return await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)

@router.put("/{signal_id}")
async def update_signal(
    signal_id: int,
    signal_update: SignalUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update signal (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        # Build updates
        updates = []
        values = []
        
        updateable = ['pair', 'direction', 'entry_price', 'stop_loss', 
                     'take_profit_1', 'take_profit_2', 'take_profit_3', 
                     'analysis', 'status', 'tp1_hit', 'tp2_hit', 'tp3_hit', 
                     'sl_hit', 'pips_gained']
        
        for field in updateable:
            value = getattr(signal_update, field, None)
            if value is not None:
                updates.append(f"{field} = ${len(values)+1}")
                values.append(value)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(signal_id)
        
        query = f"UPDATE signals SET {', '.join(updates)} WHERE id = ${len(values)} RETURNING *"
        row = await conn.fetchrow(query, *values)
        
        return dict(row)

@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete signal (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Signal not found")
        
        return {"message": "Signal deleted successfully"}

@router.post("/{signal_id}/hit-tp1")
async def mark_tp1_hit(
    signal_id: int,
    pips: Optional[float] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Mark TP1 as hit"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE signals SET tp1_hit = TRUE, pips_gained = $1, status = 'completed' 
            WHERE id = $2
        """, pips, signal_id)
        
        return {"message": "TP1 marked as hit"}

@router.post("/{signal_id}/hit-sl")
async def mark_sl_hit(
    signal_id: int,
    pips: Optional[float] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Mark Stop Loss as hit"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE signals SET sl_hit = TRUE, pips_gained = $1, status = 'stopped' 
            WHERE id = $2
        """, pips, signal_id)
        
        return {"message": "Stop Loss marked as hit"}
