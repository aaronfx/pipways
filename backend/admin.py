"""
Admin Routes
Endpoints: /api/admin/*
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from .database import db_pool
from .security import get_admin_user, get_current_user
from .schemas import UserUpdate, SignalCreate, SignalUpdate, SignalResultUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    subscription_tier: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_admin_user)
):
    """List all users (admin only)"""
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []
        param_idx = 1

        if role:
            where_clauses.append(f"role = ${param_idx}")
            params.append(role)
            param_idx += 1
        if subscription_tier:
            where_clauses.append(f"subscription_tier = ${param_idx}")
            params.append(subscription_tier)
            param_idx += 1

        where_sql = " AND ".join(where_clauses)

        rows = await conn.fetch(f"""
            SELECT 
                id, email, full_name, role, subscription_tier, subscription_status,
                email_verified, created_at, last_login
            FROM users
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params, limit, offset)

        return [dict(row) for row in rows]

@router.get("/signals")
async def list_all_signals(
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_admin_user)
):
    """List all signals for admin management (including premium)"""
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []
        param_idx = 1

        if status:
            where_clauses.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        where_sql = " AND ".join(where_clauses)

        rows = await conn.fetch(f"""
            SELECT * FROM signals 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params, limit, offset)

        return [dict(row) for row in rows]

@router.post("/signals")
async def create_signal_admin(
    signal: SignalCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new signal (admin only)"""
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

@router.put("/signals/{signal_id}")
async def update_signal_admin(
    signal_id: int,
    signal: SignalUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update signal (admin only)"""
    async with db_pool.acquire() as conn:
        updates = []
        params = []

        if signal.pair is not None:
            updates.append(f"pair = ${len(params) + 1}")
            params.append(signal.pair)
        if signal.direction is not None:
            updates.append(f"direction = ${len(params) + 1}")
            params.append(signal.direction)
        if signal.entry_price is not None:
            updates.append(f"entry_price = ${len(params) + 1}")
            params.append(signal.entry_price)
        if signal.stop_loss is not None:
            updates.append(f"stop_loss = ${len(params) + 1}")
            params.append(signal.stop_loss)
        if signal.tp1 is not None:
            updates.append(f"tp1 = ${len(params) + 1}")
            params.append(signal.tp1)
        if signal.tp2 is not None:
            updates.append(f"tp2 = ${len(params) + 1}")
            params.append(signal.tp2)
        if signal.status is not None:
            updates.append(f"status = ${len(params) + 1}")
            params.append(signal.status)
        if signal.result is not None:
            updates.append(f"result = ${len(params) + 1}")
            params.append(signal.result)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(signal_id)

        sql = f"UPDATE signals SET {', '.join(updates)} WHERE id = ${len(params)} RETURNING id"
        updated = await conn.fetchrow(sql, *params)

        if not updated:
            raise HTTPException(status_code=404, detail="Signal not found")
        return {"message": "Signal updated"}

@router.delete("/signals/{signal_id}")
async def delete_signal_admin(
    signal_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete signal (admin only)"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        if deleted == "DELETE 0":
            raise HTTPException(status_code=404, detail="Signal not found")
        return {"message": "Signal deleted"}

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_admin_user)
):
    """Get admin dashboard statistics"""
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '30 days') as new_users_30d,
                (SELECT COUNT(*) FROM users WHERE subscription_tier = 'vip') as vip_users,
                (SELECT COUNT(*) FROM signals WHERE status = 'active') as active_signals,
                (SELECT COUNT(*) FROM blog_posts WHERE status = 'published') as published_posts,
                (SELECT COUNT(*) FROM webinars WHERE scheduled_at > NOW()) as upcoming_webinars,
                (SELECT COUNT(*) FROM courses) as total_courses
        """)
        return dict(stats) if stats else {}

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update user (admin only)"""
    async with db_pool.acquire() as conn:
        updates = []
        params = []

        if user_update.role is not None:
            updates.append("role = $" + str(len(params) + 1))
            params.append(user_update.role)
        if user_update.subscription_tier is not None:
            updates.append("subscription_tier = $" + str(len(params) + 1))
            params.append(user_update.subscription_tier)
        if user_update.subscription_status is not None:
            updates.append("subscription_status = $" + str(len(params) + 1))
            params.append(user_update.subscription_status)
        if user_update.full_name is not None:
            updates.append("full_name = $" + str(len(params) + 1))
            params.append(user_update.full_name)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(user_id)

        sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ${len(params)} RETURNING id"
        updated = await conn.fetchrow(sql, *params)

        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User updated"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete user (admin only)"""
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        if deleted == "DELETE 0":
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted"}
