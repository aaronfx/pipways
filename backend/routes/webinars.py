"""
Webinar Routes - Live Trading Sessions & Training
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timedelta
import os

# ABSOLUTE IMPORTS (no dots)
import database
from schemas import (
    WebinarCreate, WebinarUpdate, WebinarResponse, 
    WebinarRegistrationResponse
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
    """Get webinars list"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            SELECT w.*, u.full_name as author_name 
            FROM webinars w
            LEFT JOIN users u ON w.created_by = u.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += f" AND w.status = ${len(params)+1}"
            params.append(status)
        
        if upcoming:
            query += " AND w.scheduled_at > CURRENT_TIMESTAMP"
            query += " AND w.scheduled_at < CURRENT_TIMESTAMP + INTERVAL '30 days'"
        
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
                is_registered = await conn.fetchrow("""
                    SELECT EXISTS(
                        SELECT 1 FROM webinar_registrations 
                        WHERE webinar_id = $1 AND user_id = $2
                    )
                """, row['id'], current_user['id'])
                webinar_dict['is_registered'] = is_registered[0] if is_registered else False
            else:
                webinar_dict['is_registered'] = False
            
            result.append(webinar_dict)
        
        return result

@router.get("/upcoming")
async def get_upcoming_webinars(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get only upcoming webinars"""
    return await get_webinars(status='scheduled', upcoming=True, current_user=current_user)

@router.get("/{webinar_id}", response_model=WebinarResponse)
async def get_webinar(
    webinar_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get single webinar details"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
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
        else:
            webinar_dict['is_registered'] = False
        
        return webinar_dict

@router.post("/{webinar_id}/register")
async def register_for_webinar(
    webinar_id: int,
    current_user: dict = Depends(get_current_user)
):
    """User registers for a webinar"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
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
        await database.log_activity(
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

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.post("/", response_model=WebinarResponse)
async def create_webinar(
    webinar: WebinarCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new webinar (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
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
        
        return await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)

@router.put("/{webinar_id}")
async def update_webinar(
    webinar_id: int,
    webinar_update: WebinarUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update webinar details (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Webinar not found")
        
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
        
        return dict(row)

@router.delete("/{webinar_id}")
async def delete_webinar(
    webinar_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete webinar (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM webinars WHERE id = $1", webinar_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Webinar not found")
        
        return {"message": "Webinar deleted successfully"}

@router.get("/admin/registrations/{webinar_id}")
async def get_webinar_registrations(
    webinar_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Get all registrations for a webinar (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        registrations = await conn.fetch("""
            SELECT wr.*, u.email, u.full_name, u.telegram_username
            FROM webinar_registrations wr
            JOIN users u ON wr.user_id = u.id
            WHERE wr.webinar_id = $1
            ORDER BY wr.registered_at DESC
        """, webinar_id)
        
        return [dict(r) for r in registrations]

@router.post("/admin/{webinar_id}/mark-attended")
async def mark_attendance(
    webinar_id: int,
    user_id: int,
    attended: bool = True,
    current_user: dict = Depends(get_admin_user)
):
    """Mark user as attended (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE webinar_registrations 
            SET attended = $1, attended_at = CASE WHEN $1 THEN CURRENT_TIMESTAMP ELSE NULL END
            WHERE webinar_id = $2 AND user_id = $3
        """, attended, webinar_id, user_id)
        
        return {"message": f"Attendance {'marked' if attended else 'unmarked'}"}

@router.post("/admin/{webinar_id}/send-reminder")
async def send_reminder(
    webinar_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_admin_user)
):
    """Send reminder to all registered users (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        webinar = await conn.fetchrow("SELECT * FROM webinars WHERE id = $1", webinar_id)
        if not webinar:
            raise HTTPException(status_code=404, detail="Webinar not found")
        
        # Get all registered users who haven't been reminded
        registrations = await conn.fetch("""
            SELECT wr.*, u.email, u.telegram_username
            FROM webinar_registrations wr
            JOIN users u ON wr.user_id = u.id
            WHERE wr.webinar_id = $1 AND wr.reminder_sent = FALSE
        """, webinar_id)
        
        # Mark reminders as sent
        await conn.execute("""
            UPDATE webinar_registrations 
            SET reminder_sent = TRUE 
            WHERE webinar_id = $1
        """, webinar_id)
        
        await database.log_activity(
            user_id=current_user['id'],
            action='send_webinar_reminders',
            entity_type='webinar',
            entity_id=webinar_id,
            new_values={"recipients_count": len(registrations)}
        )
        
        return {
            "message": f"Reminders sent to {len(registrations)} participants",
            "webinar_title": webinar['title'],
            "meeting_link": webinar['meeting_link']
        }

@router.get("/admin/dashboard-stats")
async def get_webinar_stats(current_user: dict = Depends(get_admin_user)):
    """Get webinar statistics for admin dashboard"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_webinars,
                COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as upcoming,
                COUNT(CASE WHEN status = 'live' THEN 1 END) as live_now,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                (SELECT COUNT(*) FROM webinar_registrations) as total_registrations,
                (SELECT COUNT(*) FROM webinar_registrations WHERE attended = TRUE) as total_attendees,
                (SELECT AVG(feedback_rating) FROM webinar_registrations WHERE feedback_rating IS NOT NULL) as avg_rating
            FROM webinars
            WHERE created_at > NOW() - INTERVAL '90 days'
        """)
        
        return {
            "total_webinars": stats['total_webinars'] or 0,
            "upcoming": stats['upcoming'] or 0,
            "live_now": stats['live_now'] or 0,
            "completed": stats['completed'] or 0,
            "total_registrations": stats['total_registrations'] or 0,
            "total_attendees": stats['total_attendees'] or 0,
            "average_rating": round(stats['avg_rating'], 1) if stats['avg_rating'] else 0
        }
