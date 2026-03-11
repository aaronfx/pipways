"""
Webinars Routes
Fixed: Wrapped responses
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from . import database
from .security import get_current_user_optional, get_admin_user
from .schemas import WebinarCreate

router = APIRouter()

@router.get("")
async def get_webinars(upcoming: Optional[bool] = True, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get webinars"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        if upcoming:
            webinars = await conn.fetch(
                "SELECT * FROM webinars WHERE scheduled_at > NOW() ORDER BY scheduled_at ASC"
            )
        else:
            webinars = await conn.fetch(
                "SELECT * FROM webinars ORDER BY scheduled_at DESC"
            )
        
        return {"webinars": [dict(w) for w in webinars]}

@router.get("/{webinar_id}")
async def get_webinar(webinar_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single webinar"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        webinar = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not webinar:
            raise HTTPException(status_code=404, detail="Webinar not found")
        
        return dict(webinar)

@router.post("")
async def create_webinar(webinar: WebinarCreate, current_user: dict = Depends(get_admin_user)):
    """Create webinar (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, scheduled_at, duration_minutes, meeting_link, is_premium, max_participants, reminder_message, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id
        """, webinar.title, webinar.description, webinar.scheduled_at, webinar.duration_min
