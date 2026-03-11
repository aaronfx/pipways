"""
Webinars Routes
Fixed: Wrapped responses and syntax error
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from . import database
from .security import get_current_user_optional, get_admin_user
from .schemas import WebinarCreate

router = APIRouter()

@router.get("")
async def get_webinars(upcoming: Optional[bool] = True, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get webinars with wrapped response"""
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
        query = """
            INSERT INTO webinars (
                title, description, scheduled_at, duration_minutes, 
                meeting_link, is_premium, max_participants, reminder_message, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) 
            RETURNING id
        """
        webinar_id = await conn.fetchval(
            query,
            webinar.title,
            webinar.description,
            webinar.scheduled_at,
            webinar.duration_minutes,
            webinar.meeting_link,
            webinar.is_premium,
            webinar.max_participants,
            webinar.reminder_message,
            current_user["id"]
        )
        
        return {"id": webinar_id, "message": "Webinar created successfully"}

@router.put("/{webinar_id}")
async def update_webinar(webinar_id: int, webinar: WebinarCreate, current_user: dict = Depends(get_admin_user)):
    """Update webinar (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            UPDATE webinars 
            SET title = $1, description = $2, scheduled_at = $3, duration_minutes = $4,
                meeting_link = $5, is_premium = $6, max_participants = $7, reminder_message = $8
            WHERE id = $9
        """
        await conn.execute(
            query,
            webinar.title,
            webinar.description,
            webinar.scheduled_at,
            webinar.duration_minutes,
            webinar.meeting_link,
            webinar.is_premium,
            webinar.max_participants,
            webinar.reminder_message,
            webinar_id
        )
        
        return {"message": "Webinar updated successfully"}

@router.delete("/{webinar_id}")
async def delete_webinar(webinar_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete webinar (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM webinars WHERE id = $1", webinar_id)
        return {"message": "Webinar deleted successfully"}
