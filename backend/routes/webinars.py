"""
Webinar Routes - Live Trading Sessions & Training
Includes: Registration, reminders, recordings, feedback
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timedelta
import os

from database import db_pool, log_activity, fetch, fetchrow, fetchval, execute
from schemas import (
    WebinarCreate, WebinarUpdate, WebinarResponse, 
    WebinarRegistrationResponse, UserMinimal
)
from security import get_current_user, get_current_user_optional, get_admin_user

router = APIRouter()

# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[WebinarResponse])
async def get_webinars(
    status: Optional[str] = None,
    upcoming: bool = False,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get webinars list.
    - Public access (with premium check)
    - Shows registration status for logged-in users
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        query = """
            SELECT w.*, u.full_name as author_name 
            FROM webinars w
            LEFT JOIN users u ON w.created_by = u.id
            WHERE 1=1
        """
        params = []
        
        # Filter by status
        if status:
            query += f" AND w.status = ${len(params)+1}"
            params.append(status)
        
        # Show only upcoming webinars (next 30 days)
        if upcoming:
            query += f" AND w.scheduled_at > CURRENT_TIMESTAMP"
            query += f" AND w.scheduled_at < CURRENT_TIMESTAMP + INTERVAL '30 days'"
        
        # Hide premium webinars from non-VIP users
        if not current_user or current_user.get('subscription_tier') != 'vip':
            query += " AND w.is_premium = FALSE"
        
        query += " ORDER BY w.scheduled_at ASC"
        
        webinars = await conn.fetch(query, *params)
        
        result = []
        for row in webinars:
            webinar_dict = dict(row)
            webinar_dict['author'] = {"id": row['created_by'], "full_name": row['author_name']} if row['created_by'] else None
            
            # Check if current user is registered
            if current_user:
                is_registered = await conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM webinar_registrations 
                        WHERE webinar_id = $1 AND user_id = $2
                    )
                """, row['id'], current_user['id'])
                webinar_dict['is_registered'] = is_registered
            else:
                webinar_dict['is_registered'] = False
            
            result.append(webinar_dict)
        
        return result

@router.get("/upcoming")
async def get_upcoming_webinars(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get only upcoming webinars (next 7 days)"""
    return await get_webinars(status='scheduled', upcoming=True, current_user=current_user)

@router.get("/{webinar_id}", response_model=WebinarResponse)
async def get_webinar(
    webinar_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get single webinar details"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        webinar = await conn.fetchrow("""
            SELECT w.*, u.full_name as author_name 
            FROM webinars w
            LEFT JOIN users u ON w.created_by = u.id
            WHERE w.id = $1
        """, webinar_id)
        
        if not webinar:
            raise HTTPException(status_code=404, detail="Webinar not found")
        
        # Check premium access
        if webinar['is_premium']:
            if not current_user or (current_user.get('role') not in ['admin', 'moderator'] and 
                                   current_user.get('subscription_tier') != 'vip'):
                raise HTTPException(status_code=403, detail="VIP access required")
        
        webinar_dict = dict(webinar)
        webinar_dict['author'] = {"id": webinar['created_by'], "full_name": webinar['author_name']} if webinar['created_by'] else None
        
        # Check registration status
        if current_user:
            is_registered = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM webinar_registrations 
                    WHERE webinar_id = $1 AND user_id = $2
                )
            """, webinar_id, current_user['id'])
            webinar_dict['is_registered'] = is_registered
            
            # Get user's registration details if registered
            if is_registered:
                reg = await conn.fetchrow("""
                    SELECT * FROM webinar_registrations 
                    WHERE webinar_id = $1 AND user_id = $2
                """, webinar_id, current_user['id'])
                webinar_dict['registration'] = dict(reg)
        else:
            webinar_dict['is_registered'] = False
        
        return webinar_dict

@router.post("/{webinar_id}/register")
async def register_for_webinar(
    webinar_id: int,
    current_user: dict = Depends(get_current_user)
):
    """User registers for a webinar"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        webinar = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        
        if not webinar:
            raise HTTPException(status_code=404, detail="Webinar not found")
        
        if webinar['status'] != 'scheduled':
            raise HTTPException(status_code=400, detail="Registration closed for this webinar")
        
        # Check if already registered
        existing = await conn.fetchval("""
            SELECT id FROM webinar_registrations 
            WHERE webinar_id = $1 AND user_id = $2
        """, webinar_id, current_user['id'])
        
        if existing:
            return {"message": "Already registered", "registration_id": existing}
        
        # Check capacity
        if webinar['max_participants'] and webinar['current_participants'] >= webinar['max_participants']:
            raise HTTPException(status_code=400, detail="Webinar is full")
        
        # Create registration
        registration_id = await conn.fetchval("""
            INSERT INTO webinar_registrations (webinar_id, user_id, registered_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP)
            RETURNING id
        """, webinar_id, current_user['id'])
        
        # Increment participant count
        await conn.execute("""
            UPDATE webinars 
            SET current_participants = current_participants + 1 
            WHERE id = $1
        """, webinar_id)
        
        # Log activity
        await log_activity(
            user_id=current_user['id'],
            action='webinar_register',
            entity_type='webinar',
            entity_id=webinar_id,
            new_values={"webinar_title": webinar['title']}
        )
        
        return {
            "message": "Registered successfully",
            "registration_id": registration_id,
            "meeting_link": webinar['meeting_link'] if not webinar['is_premium'] or 
                           current_user.get('subscription_tier') == 'vip' else None
        }

@router.post("/{webinar_id}/feedback")
async def submit_feedback(
    webinar_id: int,
    rating: int,
    comment: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Submit feedback for attended webinar"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1-5")
    
    async with db_pool.acquire() as conn:
        # Verify registration and attendance
        registration = await conn.fetchrow("""
            SELECT * FROM webinar_registrations 
            WHERE webinar_id = $1 AND user_id = $2
        """, webinar_id, current_user['id'])
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        if not registration['attended']:
            raise HTTPException(status_code=400, detail="You must attend the webinar before submitting feedback")
        
        # Update feedback
        await conn.execute("""
            UPDATE webinar_registrations 
            SET feedback_rating = $1, feedback_comment = $2
            WHERE webinar_id = $3 AND user_id = $4
        """, rating, comment, webinar_id, current_user['id'])
        
        return {"message": "Feedback submitted successfully"}

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.post("/", response_model=WebinarResponse)
async def create_webinar(
    webinar: WebinarCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new webinar (Admin only)"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (
                title, description, scheduled_at, duration_minutes,
                meeting_link, max_participants, reminder_message,
                is_premium, status, created_by, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP)
            RETURNING id
        """,
            webinar.title,
            webinar.description,
            webinar.scheduled_at,
            webinar.duration_minutes,
            webinar.meeting_link,
            webinar.max_participants,
            webinar.reminder_message,
            webinar.is_premium,
            'scheduled',
            current_user['id']
        )
        
        # Log activity
        await log_activity(
            user_id=current_user['id'],
            action='create_webinar',
            entity_type='webinar',
            entity_id=webinar_id,
            new_values={"title": webinar.title, "scheduled": str(webinar.scheduled_at)}
        )
        
        return await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)

@router.put("/{webinar_id}")
async def update_webinar(
    webinar_id: int,
    webinar_update: WebinarUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update webinar details (Admin only)"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Webinar not found")
        
        # Build update fields
        updates = []
        values = []
        
        updateable = ['title', 'description', 'scheduled_at', 'duration_minutes', 
                      'meeting_link', 'max_participants', 'reminder_message', 
                      'is_premium', 'status', 'recording_url']
        
        for field in updateable:
            value = getattr(webinar_update, field, None)
            if value is not None:
                updates.append(f"{field} = ${len(values)+1}")
                values.append(value)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(webinar_id)
        
        query = f"UPDATE webinars SET {', '.join(updates)} WHERE id = ${len(values)} RETURNING *"
        row = await conn.fetchrow(query, *values)
        
        # Log activity
        await log_activity(
            user_id=current_user['id'],
            action='update_webinar',
            entity_type='webinar',
            entity_id=webinar_id,
            old_values={"status": existing['status']},
            new_values={"status": row['status']}
        )
        
        return dict(row)

@router.delete("/{webinar_id}")
async def delete_webinar(
    webinar_id: int,
    current_user: dict
