"""
Media Routes - File Uploads
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
import os
import uuid
import aiofiles
from datetime import datetime

# ABSOLUTE IMPORTS (no dots)
import database
from security import get_current_user, get_admin_user

router = APIRouter()

UPLOAD_DIR = "uploads"

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = "general",
    current_user: dict = Depends(get_admin_user)
):
    """Upload file (Admin only)"""
    # Validate folder
    allowed_folders = ["blog", "courses", "signals", "avatars", "webinars", "general"]
    if folder not in allowed_folders:
        raise HTTPException(status_code=400, detail="Invalid folder")
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create folder if not exists
    folder_path = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Generate URL
    file_url = f"/uploads/{folder}/{unique_filename}"
    
    return {
        "filename": unique_filename,
        "original_name": file.filename,
        "url": file_url,
        "size": len(content),
        "folder": folder
    }

@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload user avatar"""
    # Validate image
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid image format")
    
    # Generate unique filename
    unique_filename = f"user_{current_user['id']}_{uuid.uuid4()}{file_ext}"
    
    # Save to avatars folder
    folder_path = os.path.join(UPLOAD_DIR, "avatars")
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, unique_filename)
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Update user avatar in database
    if database.db_pool:
        async with database.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET avatar_url = $1 WHERE id = $2
            """, f"/uploads/avatars/{unique_filename}", current_user['id'])
    
    return {
        "url": f"/uploads/avatars/{unique_filename}",
        "message": "Avatar uploaded successfully"
    }

@router.get("/files/{folder}/{filename}")
async def get_file(folder: str, filename: str):
    """Serve file"""
    file_path = os.path.join(UPLOAD_DIR, folder, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)
