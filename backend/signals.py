"""
Trading Signals Routes
Endpoints: /api/signals/*
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from .database import db_pool
from .security import get_current_user, get_admin_user, get_current_user_optional
from .schemas import SignalCreate, SignalUpdate, SignalResultUpdate

router = APIRouter(prefix="/api/signals", tags=["signals"])

@router.post("")
async def create_signal(
    signal: SignalCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new trading signal (admin only)"""
    async with db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (
                pair, direction, entry_price, stop_loss, tp1, tp2, 
                risk_reward_ratio, expires_at, timeframe, analysis, is_premium, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
        """, 
            signal.pair, signal.direction, signal.entry_price, signal.stop_loss,
            signal.tp1, signal.tp2, signal.risk_reward_ratio, signal.expires_at,
            signal.timeframe, signal.analysis, signal.is_premium, current_user["id"]
        )
        return {"id": signal_id, "message": "Signal created"}

@router.get("")
async def list_signals(
    status: Optional[str] = Query(None, regex="^(active|closed|expired)$"),
    pair: Optional[str] = None,
    direction: Optional[str] = Query(None, regex="^(buy|sell)$"),
    is_premium: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """List trading signals with filters"""
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []
        param_idx = 1

        if status:
            where_clauses.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        if pair:
            where_clauses.append(f"pair ILIKE ${param_idx}")
            params.append(f"%{pair}%")
            param_idx += 1
        if direction:
            where_clauses.append(f"direction = ${param_idx}")
            params.append(direction)
            param_idx += 1
        if is_premium is not None:
            where_clauses.append(f"is_premium = ${param_idx}")
            params.append(is_premium)
            param_idx += 1

        # Check premium access
        if not current_user or current_user.get("subscription_tier") not in ["vip", "premium"]:
            where_clauses.append("is_premium = FALSE")

        where_sql = " AND ".join(where_clauses)

        rows = await conn.fetch(f"""
            SELECT * FROM signals 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params, limit, offset)

        return [dict(row) for row in rows]

@router.get("/stats")
async def get_signal_stats():
    """Get signal performance statistics"""
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE result = 'WIN') as wins,
                COUNT(*) FILTER (WHERE result = 'LOSS') as losses,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COALESCE(AVG(pips_gain) FILTER (WHERE result = 'WIN'), 0) as avg_win_pips,
                COALESCE(AVG(pips_gain) FILTER (WHERE result = 'LOSS'), 0) as avg_loss_pips
            FROM signals
        """)
        return dict(stats) if stats else {}

@router.put("/{signal_id}/result")
async def update_signal_result(
    signal_id: int,
    result: SignalResultUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update signal result (admin only)"""
    async with db_pool.acquire() as conn:
        updated = await conn.fetchrow("""
            UPDATE signals 
            SET result = $1, pips_gain = $2, status = 'closed', closed_at = NOW(), updated_at = NOW()
            WHERE id = $3
            RETURNING id
        """, result.result, result.pips_gain_loss, signal_id)

        if not updated:
            raise HTTPException(status_code=404, detail="Signal not found")
        return {"message": "Signal updated"}

@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete signal (admin only)"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        if deleted == "DELETE 0":
            raise HTTPException(status_code=404, detail="Signal not found")
        return {"message": "Signal deleted"}
