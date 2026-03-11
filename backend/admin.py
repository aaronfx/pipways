"""
Admin Routes
Handles admin dashboard, user management, and content moderation
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
import os
import shutil
from datetime import datetime

# FIXED: Consistent relative imports only
from .database import db_pool, get_admin_user, get_current_user_optional
from .schemas import BlogPostCreate, CourseCreate, WebinarCreate, SignalCreate, UserUpdate

router = APIRouter()

@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_admin_user)):
    """Get dashboard statistics"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'")
        vip_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier = 'vip'")
        published_posts = await conn.fetchval("SELECT COUNT(*) FROM blog_posts WHERE status = 'published'")
        
        return {
            "total_users": total_users,
            "active_signals": active_signals,
            "vip_users": vip_users,
            "published_posts": published_posts
        }

@router.get("/users")
async def get_users(limit: int = 50, offset: int = 0, current_user: dict = Depends(get_admin_user)):
    """Get all users with pagination"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        users = await conn.fetch("""
            SELECT id, email, full_name, role, subscription_tier, subscription_status, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT $1 OFFSET $2
        """, limit, offset)
        return [dict(user) for user in users]

@router.put("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, current_user: dict = Depends(get_admin_user)):
    """Update user role or tier"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        # Build dynamic update query
        updates = []
        values = []
        if user_update.role is not None:
            updates.append("role = $1")
            values.append(user_update.role)
        if user_update.subscription_tier is not None:
            updates.append("subscription_tier = $2")
            values.append(user_update.subscription_tier)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ${len(values)}"
        await conn.execute(query, *values)
        
        return {"message": "User updated successfully"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete a user"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"message": "User deleted successfully"}

@router.get("/settings")
async def get_settings(current_user: dict = Depends(get_admin_user)):
    """Get site settings"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        settings = await conn.fetchrow("SELECT * FROM site_settings WHERE id = 1")
        return dict(settings) if settings else {}

@router.put("/settings")
async def update_settings(settings: dict, current_user: dict = Depends(get_admin_user)):
    """Update site settings"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE site_settings 
            SET site_name = $1, contact_email = $2, telegram_free_link = $3, 
                telegram_vip_link = $4, vip_price = $5, vip_price_currency = $6,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, 
            settings.get("site_name"),
            settings.get("contact_email"),
            settings.get("telegram_free_link"),
            settings.get("telegram_vip_link"),
            settings.get("vip_price"),
            settings.get("vip_price_currency")
        )
        return {"message": "Settings updated successfully"}

@router.post("/media/upload")
async def upload_media(files: List[UploadFile] = File(...), current_user: dict = Depends(get_admin_user)):
    """Upload media files"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    uploaded_urls = []
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_urls.append(f"/uploads/{file.filename}")
    
    return {"urls": uploaded_urls}

@router.get("/signals")
async def get_all_signals(current_user: dict = Depends(get_admin_user)):
    """Get all signals for admin"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        signals = await conn.fetch("""
            SELECT * FROM signals ORDER BY created_at DESC
        """)
        return [dict(signal) for signal in signals]

@router.post("/signals")
async def create_signal(signal: SignalCreate, current_user: dict = Depends(get_admin_user)):
    """Create a new signal"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (pair, direction, entry_price, stop_loss, tp1, tp2, analysis, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id
        """, 
            signal.pair, signal.direction, signal.entry_price, 
            signal.stop_loss, signal.tp1, signal.tp2,
            signal.analysis, signal.is_premium, current_user["id"]
        )
        return {"id": signal_id, "message": "Signal created successfully"}

@router.put("/signals/{signal_id}")
async def update_signal(signal_id: int, signal: SignalCreate, current_user: dict = Depends(get_admin_user)):
    """Update a signal"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE signals 
            SET pair = $1, direction = $2, entry_price = $3, stop_loss = $4, 
                tp1 = $5, tp2 = $6, analysis = $7, is_premium = $8, updated_at = CURRENT_TIMESTAMP
            WHERE id = $9
        """, 
            signal.pair, signal.direction, signal.entry_price,
            signal.stop_loss, signal.tp1, signal.tp2,
            signal.analysis, signal.is_premium, signal_id
        )
        return {"message": "Signal updated successfully"}

@router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete a signal"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM signals WHERE id = $1", signal_id)
        return {"message": "Signal deleted successfully"}
