"""
Webinars Routes
Endpoints: /api/webinars/*
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from datetime import datetime
from .database import db_pool
from .security import get_current_user, get_admin_user
from .schemas import WebinarCreate, WebinarUpdate

router = APIRouter(prefix="/api/webinars", tags=["webinars"])

@router.post("")
async def create_webinar(
    webinar: WebinarCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new webinar (admin only)"""
    async with db_pool.acquire() as conn:
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (
                title, description, scheduled_at, duration_minutes, 
                is_premium, meeting_link, max_participants, reminder_message, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """,
            webinar.title, webinar.description, webinar.scheduled_at, webinar.duration_minutes,
            webinar.is_premium, webinar.meeting_link, webinar.max_participants, 
            webinar.reminder_message, current_user["id"]
        )
        return {"id": webinar_id, "message": "Webinar created"}

@router.get("")
async def list_webinars(
    upcoming: bool = Query(False),
    is_premium: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List webinars"""
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []
        param_idx = 1

        if upcoming:
            where_clauses.append(f"scheduled_at > NOW()")
        if is_premium is not None:
            where_clauses.append(f"is_premium = ${param_idx}")
            params.append(is_premium)
            param_idx += 1

        # Check premium access
        if current_user.get("subscription_tier") not in ["vip", "premium"]:
            where_clauses.append("is_premium = FALSE")

        where_sql = " AND ".join(where_clauses)

        rows = await conn.fetch(f"""
            SELECT * FROM webinars 
            WHERE {where_sql}
            ORDER BY scheduled_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params, limit, offset)

        return [dict(row) for row in rows]

@router.put("/{webinar_id}")
async def update_webinar(
    webinar_id: int,
    webinar: WebinarUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update webinar (admin only)"""
    async with db_pool.acquire() as conn:
        # Build dynamic update
        updates = []
        params = []

        if webinar.title is not None:
            updates.append("title = $" + str(len(params) + 1))
            params.append(webinar.title)
        if webinar.description is not None:
            updates.append("description = $" + str(len(params) + 1))
            params.append(webinar.description)
        if webinar.scheduled_at is not None:
            updates.append("scheduled_at = $" + str(len(params) + 1))
            params.append(webinar.scheduled_at)
        if webinar.duration_minutes is not None:
            updates.append("duration_minutes = $" + str(len(params) + 1))
            params.append(webinar.duration_minutes)
        if webinar.is_premium is not None:
            updates.append("is_premium = $" + str(len(params) + 1))
            params.append(webinar.is_premium)
        if webinar.meeting_link is not None:
            updates.append("meeting_link = $" + str(len(params) + 1))
            params.append(webinar.meeting_link)
        if webinar.max_participants is not None:
            updates.append("max_participants = $" + str(len(params) + 1))
            params.append(webinar.max_participants)
        if webinar.reminder_message is not None:
            updates.append("reminder_message = $" + str(len(params) + 1))
            params.append(webinar.reminder_message)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(webinar_id)
        sql = f"UPDATE webinars SET {', '.join(updates)} WHERE id = ${len(params)} RETURNING id"
        updated = await conn.fetchrow(sql, *params)

        if not updated:
            raise HTTPException(status_code=404, detail="Webinar not found")
        return {"message": "Webinar updated"}

@router.delete("/{webinar_id}")
async def delete_webinar(
    webinar_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete webinar (admin only)"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM webinars WHERE id = $1", webinar_id)
        if deleted == "DELETE 0":
            raise HTTPException(status_code=404, detail="Webinar not found")
        return {"message": "Webinar deleted"}
