"""
Signal Routes - Professional Trading Signal System
Includes: CRUD, status management, R/R auto-calculation, history
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import json

from . import database
from .security import get_current_user, get_admin_user
from .schemas import SignalCreate, SignalUpdate, SignalResponse, SignalListResponse

router = APIRouter()

def calculate_risk_reward(entry: Decimal, sl: Decimal, tp1: Decimal, direction: str) -> str:
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

def calculate_pips(pair: str, entry: Decimal, exit_price: Decimal, direction: str) -> Decimal:
    """Calculate pips gained/lost"""
    try:
        diff = abs(exit_price - entry)
        # Standard pip calculation for forex
        if 'JPY' in pair:
            pips = diff * 100
        else:
            pips = diff * 10000
        return Decimal(str(pips))
    except:
        return Decimal('0')

@router.get("", response_model=SignalListResponse)
async def get_signals(
    status: Optional[str] = None,
    pair: Optional[str] = None,
    timeframe: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get signals with filtering - accessible by all authenticated users"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Build query
        query = """
            SELECT s.*, u.full_name as author_name 
            FROM signals s 
            LEFT JOIN users u ON s.created_by = u.id 
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        # Filter by status
        if status:
            query += f" AND s.status = ${param_idx}"
            params.append(status)
            param_idx += 1
        
        # Filter by pair
        if pair:
            query += f" AND s.pair ILIKE ${param_idx}"
            params.append(f"%{pair}%")
            param_idx += 1
        
        # Filter by timeframe
        if timeframe:
            query += f" AND s.timeframe = ${param_idx}"
            params.append(timeframe)
            param_idx += 1
        
        # Non-VIP users only see non-premium signals
        if current_user.get('subscription_tier') != 'vip' and current_user.get('role') != 'admin':
            query += f" AND s.is_premium = FALSE"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as count_query"
        total = await conn.fetchval(count_query, *params)
        
        # Add pagination
        query += f" ORDER BY s.created_at DESC OFFSET ${param_idx} LIMIT ${param_idx + 1}"
        params.append((page - 1) * limit)
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        
        signals = []
        for row in rows:
            signal = dict(row)
            signal['author'] = {"id": row['created_by'], "full_name": row['author_name']} if row['created_by'] else None
            signals.append(signal)
        
        return {
            "signals": signals,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

@router.get("/active", response_model=SignalListResponse)
async def get_active_signals(current_user: dict = Depends(get_current_user)):
    """Get currently active signals"""
    return await get_signals(status="active", page=1, limit=50, current_user=current_user)

@router.get("/history", response_model=SignalListResponse)
async def get_signal_history(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get signal history for last N days"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        since = datetime.now() - timedelta(days=days)
        
        rows = await conn.fetch("""
            SELECT s.*, u.full_name as author_name 
            FROM signals s 
            LEFT JOIN users u ON s.created_by = u.id 
            WHERE s.created_at > $1
            ORDER BY s.created_at DESC
        """, since)
        
        signals = []
        for row in rows:
            signal = dict(row)
            signal['author'] = {"id": row['created_by'], "full_name": row['author_name']} if row['created_by'] else None
            signals.append(signal)
        
        return {
            "signals": signals,
            "total": len(signals),
            "page": 1,
            "pages": 1
        }

@router.get("/pairs")
async def get_all_pairs(current_user: dict = Depends(get_current_user)):
    """Get list of all trading pairs with signal counts"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT pair, COUNT(*) as count,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count
            FROM signals 
            GROUP BY pair 
            ORDER BY count DESC
        """)
        return [{"pair": r["pair"], "total": r["count"], "active": r["active_count"]} for r in rows]

@router.post("", response_model=SignalResponse)
async def create_signal(
    signal: SignalCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new trading signal (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Auto-calculate R/R ratio
    rr_ratio = calculate_risk_reward(
        signal.entry_price, 
        signal.stop_loss, 
        signal.tp1, 
        signal.direction
    )
    
    async with database.db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (
                pair, direction, entry_price, stop_loss, tp1, tp2, tp3,
                timeframe, risk_reward_ratio, analysis, chart_image_url,
                is_premium, status, created_by, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
            RETURNING id
        """,
            signal.pair,
            signal.direction,
            signal.entry_price,
            signal.stop_loss,
            signal.tp1,
            signal.tp2,
            signal.tp3,
            signal.timeframe,
            rr_ratio,
            signal.analysis,
            signal.chart_image_url,
            signal.is_premium,
            "active",
            current_user['id']
        )
        
        # Log activity
        await database.log_activity(
            current_user['id'],
            'create_signal',
            'signal',
            signal_id,
            None,
            {"pair": signal.pair, "direction": signal.direction},
            None, None
        )
        
        # Return created signal
        row = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        return dict(row)

@router.put("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: int,
    signal: SignalUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update signal details (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Check exists
        existing = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        # Build update fields
        updates = []
        values = []
        param_idx = 1
        
        updateable_fields = [
            'pair', 'direction', 'entry_price', 'stop_loss', 'tp1', 'tp2', 'tp3',
            'timeframe', 'analysis', 'chart_image_url', 'is_premium', 'status',
            'tp1_hit', 'tp2_hit', 'tp3_hit', 'sl_hit', 'pips_gained'
        ]
        
        for field in updateable_fields:
            value = getattr(signal, field)
            if value is not None:
                updates.append(f"{field} = ${param_idx}")
                values.append(value)
                param_idx += 1
        
        # Recalculate R/R if entry/sl/tp1 changed
        if any(getattr(signal, f) is not None for f in ['entry_price', 'stop_loss', 'tp1', 'direction']):
            entry = signal.entry_price or existing['entry_price']
            sl = signal.stop_loss or existing['stop_loss']
            tp1 = signal.tp1 or existing['tp1']
            direction = signal.direction or existing['direction']
            rr_ratio = calculate_risk_reward(entry, sl, tp1, direction)
            if rr_ratio:
                updates.append(f"risk_reward_ratio = ${param_idx}")
                values.append(rr_ratio)
                param_idx += 1
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append(f"updated_at = NOW()")
        values.append(signal_id)
        
        query = f"UPDATE signals SET {', '.join(updates)} WHERE id = ${param_idx} RETURNING *"
        row = await conn.fetchrow(query, *values)
        
        # Log activity
        await database.log_activity(
            current_user['id'],
            'update_signal',
            'signal',
            signal_id,
            dict(existing),
            dict(row),
            None, None
        )
        
        return dict(row)

@router.post("/{signal_id}/update-status")
async def update_signal_status(
    signal_id: int,
    status: str,
    exit_price: Optional[Decimal] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Update signal status (TP1_HIT, TP2_HIT, SL_HIT, CLOSED)"""
    if status not in ['tp1_hit', 'tp2_hit', 'tp3_hit', 'sl_hit', 'closed', 'active', 'expired']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM signals WHERE id = $1", signal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        # Build update based on status
        updates = {"status": status, "updated_at": datetime.now()}
        
        if status == 'tp1_hit':
            updates['tp1_hit'] = True
            updates['hit_date'] = datetime.now()
        elif status == 'tp2_hit':
            updates['tp2_hit'] = True
            updates['hit_date'] = datetime.now()
        elif status == 'tp3_hit':
            updates['tp3_hit'] = True
            updates['hit_date'] = datetime.now()
        elif status == 'sl_hit':
            updates['sl_hit'] = True
            updates['hit_date'] = datetime.now()
        
        # Calculate pips if exit price provided
        if exit_price and existing['entry_price']:
            pips = calculate_pips(
                existing['pair'],
                existing['entry_price'],
                exit_price,
                existing['direction']
            )
            updates['pips_gained'] = pips if status != 'sl_hit' else -pips
        
        if status in ['tp1_hit', 'tp2_hit', 'tp3_hit', 'sl_hit', 'closed', 'expired']:
            updates['closed_at'] = datetime.now()
        
        # Build SQL
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
        values = list(updates.values())
        
        await conn.execute(
            f"UPDATE signals SET {set_clause} WHERE id = $1",
            signal_id,
            *values
        )
        
        # Log activity
        await database.log_activity(
            current_user['id'],
            'update_signal_status',
            'signal',
            signal_id,
            {"status": existing['status']},
            {"status": status},
            None, None
        )
        
        return {"message": f"Signal updated to {status}", "signal_id": signal_id}

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
        
        await database.log_activity(
            current_user['id'],
            'delete_signal',
            'signal',
            signal_id,
            None, None,
            None, None
        )
        
        return {"message": "Signal deleted successfully"}

@router.get("/stats/overview")
async def get_signal_stats(current_user: dict = Depends(get_current_user)):
    """Get signal performance statistics"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN tp1_hit = true THEN 1 END) as tp1_hits,
                COUNT(CASE WHEN tp2_hit = true THEN 1 END) as tp2_hits,
                COUNT(CASE WHEN tp3_hit = true THEN 1 END) as tp3_hits,
                COUNT(CASE WHEN sl_hit = true THEN 1 END) as sl_hits,
                AVG(CASE WHEN pips_gained IS NOT NULL THEN pips_gained END) as avg_pips,
                SUM(CASE WHEN pips_gained > 0 THEN pips_gained ELSE 0 END) as total_profit_pips,
                SUM(CASE WHEN pips_gained < 0 THEN pips_gained ELSE 0 END) as total_loss_pips
            FROM signals
            WHERE created_at > NOW() - INTERVAL '30 days'
        """)
        
        return dict(stats)
