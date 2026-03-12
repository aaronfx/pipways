import os
import uuid
import magic
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy import select, insert, delete
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import database, media_files
from .security import get_current_user, get_current_admin

router = APIRouter(prefix="/media", tags=["media"])
limiter = Limiter(key_func=get_remote_address)

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
    "text/csv": ".csv",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/json": ".json"
}

os.makedirs(UPLOAD_DIR, exist_ok=True)

class MediaResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_type: str
    file_size: int
    mime_type: str
    uploaded_by: int
    created_at: datetime
    url: str

@router.get("/", response_model=List[MediaResponse])
async def get_media(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    query = select(media_files).where(
        media_files.c.uploaded_by == current_user["id"]
    ).limit(limit).offset(offset)
    results = await database.fetch_all(query)

    response = []
    for row in results:
        data = dict(row)
        data["url"] = f"/uploads/{data['filename']}"
        response.append(data)
    return response

@router.post("/upload")
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    mime_type = magic.from_buffer(contents, mime=True)
    if mime_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File type not allowed: {mime_type}"
        )

    file_ext = ALLOWED_TYPES[mime_type]
    safe_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    query = insert(media_files).values(
        filename=safe_filename,
        original_name=file.filename,
        file_path=file_path,
        file_type=file_ext.replace(".", ""),
        file_size=len(contents),
        mime_type=mime_type,
        uploaded_by=current_user["id"],
        created_at=datetime.utcnow()
    )
    media_id = await database.execute(query)

    return {
        "id": media_id,
        "filename": safe_filename,
        "original_name": file.filename,
        "url": f"/uploads/{safe_filename}",
        "size": len(contents),
        "mime_type": mime_type
    }

@router.delete("/{media_id}")
async def delete_media(
    media_id: int,
    current_user: dict = Depends(get_current_user)
):
    query = select(media_files).where(media_files.c.id == media_id)
    media = await database.fetch_one(query)

    if not media:
        raise HTTPException(status_code=404, detail="File not found")

    if media["uploaded_by"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        if os.path.exists(media["file_path"]):
            os.remove(media["file_path"])
    except Exception:
        pass

    query = delete(media_files).where(media_files.c.id == media_id)
    await database.execute(query)

    return {"message": "File deleted successfully"}
