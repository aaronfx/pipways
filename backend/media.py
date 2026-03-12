"""
Media file uploads and management.
"""
from fastapi import APIRouter, Depends, UploadFile, File
from backend.security import get_current_user

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload media file."""
    return {"filename": file.filename, "status": "uploaded"}
