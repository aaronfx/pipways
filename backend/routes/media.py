"""
Media Upload Routes
Handles images, videos, and documents for all modules
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
import os
import uuid
import aiofiles
from pathlib import Path

from .security import get_current_user, get_admin_user
from . import database

router = APIRouter()

UPLOAD_DIR = Path("uploads")
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/webm', 'video/quicktime'}
ALLOWED_DOC_TYPES = {'application/pdf'}
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.pdf'}

def get_upload_path(entity_type: str) -> Path:
    """Get upload directory for entity type"""
    path = UPLOAD_DIR / entity_type
    path.mkdir(parents=True, exist_ok=True)
    return path

def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate file type and size"""
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type {ext} not allowed"
    
    # Check content type
    allowed = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_DOC_TYPES
    if file.content_type not in allowed:
        return False, f"Content type {file.content_type} not allowed"
    
    return True, ""

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    entity_type: str = Form(...),  # 'signals', 'courses', 'blog', 'general'
    entity_id: Optional[int] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file"""
    valid, error = validate_file(file)
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Generate unique filename
    ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4()}{ext}"
    
    # Determine subdirectory based on type
    if file.content_type in ALLOWED_IMAGE_TYPES:
        subdir = "images"
    elif file.content_type in ALLOWED_VIDEO_TYPES:
        subdir = "videos"
    else:
        subdir = "documents"
    
    upload_path = get_upload_path(f"{entity_type}/{subdir}")
    file_path = upload_path / unique_name
    
    # Save file
    try:
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Generate URL
    file_url = f"/uploads/{entity_type}/{subdir}/{unique_name}"
    
    # Save to database
    if database.db_pool:
        async with database.db_pool.acquire() as conn:
            media_id = await conn.fetchval("""
                INSERT INTO media_files (filename, original_name, url, mime_type, file_size_bytes, entity_type, entity_id, uploaded_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, unique_name, file.filename, file_url, file.content_type, len(content), entity_type, entity_id, current_user['id'])
    
    return {
        "id": media_id if database.db_pool else None,
        "url": file_url,
        "filename": unique_name,
        "original_name": file.filename,
        "size": len(content),
        "type": file.content_type
    }

@router.delete("/{media_id}")
async def delete_file(
    media_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete a file"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        media = await conn.fetchrow("SELECT * FROM media_files WHERE id = $1", media_id)
        if not media:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete physical file
        try:
            file_path = UPLOAD_DIR / media['url'].replace('/uploads/', '')
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            # Log but continue
            print(f"Error deleting file: {e}")
        
        # Delete database record
        await conn.execute("DELETE FROM media_files WHERE id = $1", media_id)
        
        return {"message": "File deleted successfully"}
