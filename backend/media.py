"""
Media Upload Routes
Endpoints: /api/media/*
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os
import uuid
import shutil
from .database import db_pool, UPLOAD_DIR
from .security import get_current_user, get_admin_user

router = APIRouter(prefix="/api/media", tags=["media"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload media file"""
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = os.path.getsize(file_path)

    # Store in database
    async with db_pool.acquire() as conn:
        media_id = await conn.fetchval("""
            INSERT INTO media_files (filename, url, file_type, size_bytes, uploaded_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, file.filename, f"/uploads/{unique_name}", file.content_type, file_size, current_user["id"])

    return {
        "id": media_id,
        "filename": file.filename,
        "url": f"/uploads/{unique_name}",
        "size": file_size
    }

@router.get("")
async def list_media(
    limit: int = 50,
    current_user: dict = Depends(get_admin_user)
):
    """List uploaded media (admin only)"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT m.*, u.full_name as uploader_name
            FROM media_files m
            JOIN users u ON m.uploaded_by = u.id
            ORDER BY m.created_at DESC
            LIMIT $1
        """, limit)
        return [dict(row) for row in rows]

@router.delete("/{media_id}")
async def delete_media(
    media_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete media file (admin only)"""
    async with db_pool.acquire() as conn:
        media = await conn.fetchrow("SELECT * FROM media_files WHERE id = $1", media_id)
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")

        # Delete file from disk
        file_path = os.path.join(UPLOAD_DIR, os.path.basename(media["url"]))
        if os.path.exists(file_path):
            os.remove(file_path)

        await conn.execute("DELETE FROM media_files WHERE id = $1", media_id)
        return {"message": "Media deleted"}
