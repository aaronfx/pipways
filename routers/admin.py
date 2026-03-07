from fastapi import APIRouter, Form, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from typing import Optional
import json
from datetime import datetime
from pathlib import Path
import uuid

from auth import get_current_admin
from database import get_db
from config import settings

router = APIRouter()

MEDIA_DIR = Path(settings.UPLOAD_DIR) / "media"

@router.get("/dashboard")
async def admin_dashboard(
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Admin dashboard analytics"""
    try:
        # User statistics
        user_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_users_7d,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as new_users_30d
            FROM users
        """)

        # Trade statistics
        trade_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as trades_7d,
                SUM(pips) as total_pips
            FROM trades
        """)

        # Blog statistics
        blog_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_posts,
                COUNT(*) FILTER (WHERE status = 'published') as published_posts,
                SUM(view_count) as total_views
            FROM blog_posts
        """)

        # Analysis statistics
        analysis_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_analyses,
                AVG(trader_score) as avg_trader_score
            FROM trade_analysis_uploads
        """)

        # Recent activity
        recent_users = await conn.fetch("""
            SELECT id, name, email, created_at FROM users
            ORDER BY created_at DESC LIMIT 5
        """)

        recent_trades = await conn.fetch("""
            SELECT t.*, u.name as user_name 
            FROM trades t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC LIMIT 5
        """)

        return {
            "users": dict(user_stats) if user_stats else {},
            "trades": dict(trade_stats) if trade_stats else {},
            "blog": dict(blog_stats) if blog_stats else {},
            "analyses": dict(analysis_stats) if analysis_stats else {},
            "recent_activity": {
                "users": [dict(u) for u in recent_users],
                "trades": [dict(t) for t in recent_trades]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    conn=Depends(get_db)
):
    """List all users (admin only)"""
    try:
        offset = (page - 1) * per_page

        where_clause = ""
        params = []
        if search:
            where_clause = "WHERE name ILIKE $1 OR email ILIKE $1"
            params.append(f"%{search}%")

        users = await conn.fetch(f"""
            SELECT id, name, email, is_admin, created_at,
                   (SELECT COUNT(*) FROM trades WHERE user_id = users.id) as trade_count,
                   (SELECT COUNT(*) FROM trade_analysis_uploads WHERE user_id = users.id) as analysis_count
            FROM users
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params)+1} OFFSET ${len(params)+2}
        """, *params, per_page, offset)

        count = await conn.fetchrow(f"SELECT COUNT(*) as total FROM users {where_clause}", *params)

        return {
            "users": [dict(u) for u in users],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": count['total'] if count else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}")
async def admin_update_user(
    user_id: int,
    is_admin: Optional[bool] = Form(None),
    conn=Depends(get_db)
):
    """Update user (admin only)"""
    try:
        updates = []
        params = []

        if is_admin is not None:
            updates.append(f"is_admin = ${len(params)+1}")
            params.append(is_admin)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(user_id)

        await conn.execute(f"""
            UPDATE users SET {', '.join(updates)} WHERE id = ${len(params)}
        """, *params)

        return {"success": True, "message": "User updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Media management
@router.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Upload media file (admin only)"""
    try:
        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = MEDIA_DIR / unique_filename

        with open(file_path, "wb") as f:
            f.write(contents)

        file_type = ext.replace('.', '')

        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

        media_id = await conn.fetchval("""
            INSERT INTO media_files 
            (filename, original_name, file_path, file_type, file_size, mime_type, alt_text, uploaded_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            unique_filename,
            file.filename,
            str(file_path),
            file_type,
            file_size,
            file.content_type or "application/octet-stream",
            alt_text,
            user["id"]
        )

        return {
            "success": True,
            "media_id": media_id,
            "filename": unique_filename,
            "url": f"/media/{unique_filename}",
            "size": file_size
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media")
async def list_media(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conn=Depends(get_db)
):
    """List all media files (admin only)"""
    try:
        offset = (page - 1) * per_page
        media = await conn.fetch("""
            SELECT m.*, u.name as uploaded_by_name
            FROM media_files m
            JOIN users u ON m.uploaded_by = u.id
            ORDER BY m.created_at DESC
            LIMIT $1 OFFSET $2
        """, per_page, offset)

        count = await conn.fetchrow("SELECT COUNT(*) as total FROM media_files")

        return {
            "media": [dict(m) for m in media],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": count['total'] if count else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/media/{filename}")
async def serve_media(filename: str):
    """Serve media file"""
    file_path = MEDIA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
