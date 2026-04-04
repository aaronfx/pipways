"""
backend/media.py — CMS media library for Gopipways.

Storage: PostgreSQL (base64 in media_files table).
Files persist across Railway deployments because the Railway PostgreSQL
database is persistent, unlike the container filesystem.

No external packages required. Works immediately after deploy.

Endpoints (mounted at /cms/media in main.py):
    POST   /cms/media/upload
    GET    /cms/media
    GET    /cms/media?folder=blog
    DELETE /cms/media?filename=...
    GET    /cms/media/serve/{filename:path}
"""

import os
import re
import uuid
import base64
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response

from backend.database import database
from backend.security import get_current_user, is_admin_user

router = APIRouter(redirect_slashes=False)

# ── Config ────────────────────────────────────────────────────────────────────

MEDIA_MAX_MB   = int(os.getenv("MEDIA_MAX_MB", "20"))
MAX_BYTES      = MEDIA_MAX_MB * 1024 * 1024
MEDIA_BASE_URL = os.getenv(
    "MEDIA_BASE_URL",
    "https://www.gopipways.com/cms/media/serve"
)

ALLOWED_TYPES = {
    "image/jpeg":      "images",
    "image/png":       "images",
    "image/webp":      "images",
    "image/gif":       "images",
    "image/svg+xml":   "images",
    "video/mp4":       "video",
    "video/webm":      "video",
    "application/pdf": "docs",
}

# ── DB table ──────────────────────────────────────────────────────────────────

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS media_files (
    id          SERIAL PRIMARY KEY,
    filename    VARCHAR(512) UNIQUE NOT NULL,
    original    VARCHAR(255) NOT NULL,
    mime_type   VARCHAR(100) NOT NULL,
    folder      VARCHAR(50)  NOT NULL DEFAULT 'general',
    size_bytes  INTEGER      NOT NULL DEFAULT 0,
    url         TEXT         NOT NULL,
    data        TEXT,
    uploaded_by INTEGER,
    created_at  TIMESTAMPTZ  DEFAULT NOW()
)
"""
_TABLE_READY = False

async def _ensure_table():
    global _TABLE_READY
    if _TABLE_READY:
        return
    try:
        await database.execute(_TABLE_SQL)
        _TABLE_READY = True
    except Exception as e:
        print(f"[MEDIA] Table init warning: {e}", flush=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_filename(original: str, folder: str) -> str:
    ext  = Path(original).suffix.lower()
    stem = re.sub(r"[^a-z0-9_-]", "_", Path(original).stem.lower())[:40]
    uid  = uuid.uuid4().hex[:8]
    return f"{folder}/{stem}_{uid}{ext}"

def _public_url(filename: str) -> str:
    return f"{MEDIA_BASE_URL.rstrip('/')}/{filename}"

def _get_user_id(current_user) -> int:
    try:
        return current_user.get("id", 0) if hasattr(current_user, "get") else int(current_user["id"])
    except Exception:
        return 0


# ── POST /cms/media/upload ────────────────────────────────────────────────────

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    await _ensure_table()

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type in ("application/octet-stream", ""):
        guessed, _ = mimetypes.guess_type(file.filename or "")
        content_type = guessed or "application/octet-stream"

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            400,
            f"File type '{content_type}' not allowed. "
            f"Allowed: {', '.join(ALLOWED_TYPES)}"
        )

    data = await file.read()

    if not data:
        raise HTTPException(400, "Uploaded file is empty")
    if len(data) > MAX_BYTES:
        raise HTTPException(
            400,
            f"File too large ({len(data) // 1024 // 1024} MB). Max: {MEDIA_MAX_MB} MB"
        )

    original = file.filename or "upload"
    folder   = ALLOWED_TYPES[content_type]
    filename = _safe_filename(original, folder)
    url      = _public_url(filename)
    user_id  = _get_user_id(current_user)
    b64      = base64.b64encode(data).decode()

    try:
        await database.execute(
            """
            INSERT INTO media_files
                (filename, original, mime_type, folder, size_bytes, url, data, uploaded_by)
            VALUES (:fn, :orig, :mime, :folder, :size, :url, :data, :uid)
            ON CONFLICT (filename) DO UPDATE
                SET data=EXCLUDED.data, size_bytes=EXCLUDED.size_bytes, url=EXCLUDED.url
            """,
            {"fn": filename, "orig": original, "mime": content_type,
             "folder": folder, "size": len(data), "url": url,
             "data": b64, "uid": user_id}
        )
    except Exception as e:
        print(f"[MEDIA] DB insert error: {e}", flush=True)
        raise HTTPException(500, f"Failed to store file: {e}")

    print(f"[MEDIA] Uploaded {original} -> {filename} ({len(data)} bytes)", flush=True)

    return {
        "success":       True,
        "url":           url,
        "filename":      filename,
        "original_name": original,
        "folder":        folder,
        "size":          len(data),
        "mime_type":     content_type,
    }


# ── GET /cms/media ────────────────────────────────────────────────────────────

@router.get("")
async def list_media(
    folder: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    await _ensure_table()

    try:
        sql = """
            SELECT filename, original AS original_name, mime_type, folder,
                   size_bytes AS size, url, created_at
            FROM media_files
        """
        params: dict = {}
        if folder and folder != "all":
            sql   += " WHERE folder = :folder"
            params = {"folder": folder}
        sql += " ORDER BY created_at DESC LIMIT 200"
        rows  = await database.fetch_all(sql, params)
        items = [dict(r) for r in rows]
    except Exception as e:
        print(f"[MEDIA] List error: {e}", flush=True)
        items = []

    return {"files": items, "count": len(items), "folder": folder or "all"}


# ── DELETE /cms/media ─────────────────────────────────────────────────────────

@router.delete("")
async def delete_media(
    filename: str = Query(...),
    current_user=Depends(get_current_user),
):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    filename = filename.lstrip("/")
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(400, "Invalid filename")

    await _ensure_table()

    try:
        await database.execute(
            "DELETE FROM media_files WHERE filename = :fn",
            {"fn": filename}
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to delete: {e}")

    return {"success": True, "deleted": filename}


# ── GET /cms/media/serve/{filename:path} ──────────────────────────────────────

@router.get("/serve/{filename:path}")
async def serve_media(filename: str):
    """Serve a stored media file publicly (no auth required)."""
    filename = filename.lstrip("/")
    if ".." in filename:
        raise HTTPException(400, "Invalid path")

    await _ensure_table()

    try:
        row = await database.fetch_one(
            "SELECT data, mime_type FROM media_files WHERE filename = :fn",
            {"fn": filename}
        )
        if row and row["data"]:
            return Response(
                content=base64.b64decode(row["data"]),
                media_type=row["mime_type"] or "application/octet-stream",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as e:
        print(f"[MEDIA] Serve error: {e}", flush=True)

    raise HTTPException(404, "File not found")
