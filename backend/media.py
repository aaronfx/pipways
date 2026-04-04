"""
Media file uploads and management.

Endpoints (all mounted under /cms by main.py):
  POST   /cms/media/upload          — upload a file (admin only)
  GET    /cms/media                 — list uploaded files (admin only)
  GET    /cms/media?folder=blog     — list by folder
  DELETE /cms/media?filename=...    — delete a file (admin only)
  GET    /cms/media/serve/{filename} — serve a file publicly (no auth)

Storage: files are written to MEDIA_ROOT (default: /app/uploads).
  On Railway the filesystem is ephemeral — files survive restarts but
  NOT new deployments. For persistence, set MEDIA_STORAGE=db to store
  files as base64 in the database, or point MEDIA_ROOT at a mounted volume.

Environment variables:
  MEDIA_ROOT      — absolute path to store files (default: /app/uploads)
  MEDIA_BASE_URL  — public URL prefix served to clients
                    (default: https://www.gopipways.com/cms/media/serve)
  MEDIA_MAX_MB    — max upload size in MB (default: 10)
  MEDIA_STORAGE   — "disk" (default) | "db"
"""

import os
import re
import uuid
import base64
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response

from .database import database
from .security import get_current_user, is_admin_user, get_user_id

router = APIRouter()

# ── Config ─────────────────────────────────────────────────────────────────────

MEDIA_ROOT     = Path(os.getenv("MEDIA_ROOT", "/app/uploads"))
MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "https://www.gopipways.com/cms/media/serve")
MEDIA_MAX_MB   = int(os.getenv("MEDIA_MAX_MB", "10"))
MEDIA_STORAGE  = os.getenv("MEDIA_STORAGE", "disk").lower()  # "disk" | "db"

# Allowed MIME types → sub-folder mapping
ALLOWED_TYPES: dict[str, str] = {
    # Images
    "image/jpeg":   "images",
    "image/png":    "images",
    "image/gif":    "images",
    "image/webp":   "images",
    "image/svg+xml":"images",
    # Documents
    "application/pdf": "docs",
    # Video (for lesson attachments — large files should use YouTube instead)
    "video/mp4":    "video",
    "video/webm":   "video",
}

MAX_BYTES = MEDIA_MAX_MB * 1024 * 1024


# ── DB table (created once on first use) ───────────────────────────────────────

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS media_files (
    id          SERIAL PRIMARY KEY,
    filename    VARCHAR(255) UNIQUE NOT NULL,
    original    VARCHAR(255) NOT NULL,
    mime_type   VARCHAR(100) NOT NULL,
    folder      VARCHAR(50)  NOT NULL DEFAULT 'general',
    size_bytes  INTEGER      NOT NULL DEFAULT 0,
    url         TEXT         NOT NULL,
    data        TEXT,                          -- base64 payload (db mode only)
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_filename(original: str, folder: str) -> str:
    """Generate a unique, filesystem-safe filename preserving the extension."""
    ext  = Path(original).suffix.lower()
    stem = re.sub(r"[^a-z0-9_-]", "_", Path(original).stem.lower())[:40]
    uid  = uuid.uuid4().hex[:8]
    return f"{folder}/{stem}_{uid}{ext}"


def _public_url(filename: str) -> str:
    return f"{MEDIA_BASE_URL.rstrip('/')}/{filename}"


async def _save_disk(filename: str, data: bytes) -> None:
    """Write bytes to MEDIA_ROOT / filename, creating directories as needed."""
    dest = MEDIA_ROOT / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


async def _save_db(filename: str, mime: str, data: bytes, folder: str, original: str,
                   size: int, url: str, user_id: int) -> None:
    """Store file content as base64 in media_files table."""
    b64 = base64.b64encode(data).decode()
    await database.execute(
        """
        INSERT INTO media_files (filename, original, mime_type, folder, size_bytes, url, data, uploaded_by)
        VALUES (:fn, :orig, :mime, :folder, :size, :url, :data, :uid)
        ON CONFLICT (filename) DO UPDATE
            SET data=EXCLUDED.data, size_bytes=EXCLUDED.size_bytes, url=EXCLUDED.url
        """,
        {"fn": filename, "orig": original, "mime": mime, "folder": folder,
         "size": size, "url": url, "data": b64, "uid": user_id}
    )


# ── POST /cms/media/upload ─────────────────────────────────────────────────────

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """Upload a media file. Admin only."""
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    await _ensure_table()

    # ── 1. Validate MIME type ──────────────────────────────────────────────
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    # Fall back to guessing from extension if browser sends octet-stream
    if content_type == "application/octet-stream" or not content_type:
        guessed, _ = mimetypes.guess_type(file.filename or "")
        content_type = guessed or "application/octet-stream"

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            400,
            f"File type '{content_type}' is not allowed. "
            f"Allowed: {', '.join(ALLOWED_TYPES)}"
        )

    folder = ALLOWED_TYPES[content_type]

    # ── 2. Read and validate size ──────────────────────────────────────────
    data = await file.read()
    size = len(data)

    if size == 0:
        raise HTTPException(400, "Uploaded file is empty")
    if size > MAX_BYTES:
        raise HTTPException(
            400,
            f"File too large ({size // 1024 // 1024} MB). "
            f"Maximum allowed: {MEDIA_MAX_MB} MB"
        )

    # ── 3. Generate safe filename and public URL ───────────────────────────
    original = file.filename or "upload"
    filename = _safe_filename(original, folder)
    url      = _public_url(filename)
    user_id  = get_user_id(current_user)

    # ── 4. Store ───────────────────────────────────────────────────────────
    try:
        if MEDIA_STORAGE == "db":
            await _save_db(filename, content_type, data, folder, original,
                           size, url, user_id)
        else:
            await _save_disk(filename, data)
            # Also log in DB (without the blob) for listing/management
            try:
                await database.execute(
                    """
                    INSERT INTO media_files
                        (filename, original, mime_type, folder, size_bytes, url, uploaded_by)
                    VALUES (:fn, :orig, :mime, :folder, :size, :url, :uid)
                    ON CONFLICT (filename) DO UPDATE
                        SET size_bytes=EXCLUDED.size_bytes, url=EXCLUDED.url
                    """,
                    {"fn": filename, "orig": original, "mime": content_type,
                     "folder": folder, "size": size, "url": url, "uid": user_id}
                )
            except Exception as db_err:
                print(f"[MEDIA] DB log warning (non-fatal): {db_err}", flush=True)

    except Exception as e:
        print(f"[MEDIA] Storage error: {e}", flush=True)
        raise HTTPException(500, f"Failed to store file: {e}")

    print(f"[MEDIA] ✅ Uploaded {original} → {filename} ({size} bytes, {content_type})", flush=True)

    return {
        "success":   True,
        "filename":  filename,
        "original":  original,
        "url":       url,
        "mime_type": content_type,
        "folder":    folder,
        "size":      size,
    }


# ── GET /cms/media ─────────────────────────────────────────────────────────────

@router.get("")
async def list_media(
    folder: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
):
    """List uploaded media files. Admin only."""
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    await _ensure_table()

    if MEDIA_STORAGE == "disk":
        # Build list from filesystem + DB records merged
        items = []
        try:
            sql = "SELECT filename, original, mime_type, folder, size_bytes, url, created_at FROM media_files"
            params: dict = {}
            if folder and folder != "all":
                sql += " WHERE folder = :folder"
                params["folder"] = folder
            sql += " ORDER BY created_at DESC LIMIT 200"
            rows = await database.fetch_all(sql, params)
            items = [dict(r) for r in rows]
        except Exception as e:
            print(f"[MEDIA] List DB error: {e}", flush=True)

        # Also scan disk in case DB log is behind
        scan_root = MEDIA_ROOT / (folder if folder and folder != "all" else "")
        if scan_root.exists():
            db_names = {i["filename"] for i in items}
            for p in scan_root.rglob("*"):
                if p.is_file():
                    rel = str(p.relative_to(MEDIA_ROOT))
                    if rel not in db_names:
                        mime, _ = mimetypes.guess_type(str(p))
                        items.append({
                            "filename":   rel,
                            "original":   p.name,
                            "mime_type":  mime or "application/octet-stream",
                            "folder":     p.parent.name,
                            "size_bytes": p.stat().st_size,
                            "url":        _public_url(rel),
                            "created_at": None,
                        })

    else:
        # DB mode — all data in media_files
        try:
            sql = "SELECT filename, original, mime_type, folder, size_bytes, url, created_at FROM media_files"
            params = {}
            if folder and folder != "all":
                sql += " WHERE folder = :folder"
                params["folder"] = folder
            sql += " ORDER BY created_at DESC LIMIT 200"
            rows = await database.fetch_all(sql, params)
            items = [dict(r) for r in rows]
        except Exception as e:
            print(f"[MEDIA] List error: {e}", flush=True)
            items = []

    return {"files": items, "count": len(items), "folder": folder or "all"}


# ── DELETE /cms/media ──────────────────────────────────────────────────────────

@router.delete("")
async def delete_media(
    filename: str = Query(..., description="Relative filename, e.g. images/photo_abc123.jpg"),
    current_user=Depends(get_current_user),
):
    """Delete a media file. Admin only."""
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    await _ensure_table()

    # Sanitise — prevent path traversal
    filename = filename.lstrip("/")
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(400, "Invalid filename")

    deleted_disk = False
    deleted_db   = False

    # Remove from disk
    if MEDIA_STORAGE != "db":
        target = MEDIA_ROOT / filename
        if target.exists() and target.is_file():
            target.unlink()
            deleted_disk = True
            print(f"[MEDIA] Deleted from disk: {filename}", flush=True)

    # Remove from DB
    try:
        result = await database.execute(
            "DELETE FROM media_files WHERE filename = :fn",
            {"fn": filename}
        )
        deleted_db = True
    except Exception as e:
        print(f"[MEDIA] DB delete warning: {e}", flush=True)

    if not deleted_disk and not deleted_db:
        raise HTTPException(404, f"File not found: {filename}")

    return {"success": True, "deleted": filename}


# ── GET /cms/media/serve/{filename:path} ───────────────────────────────────────

@router.get("/serve/{filename:path}")
async def serve_media(filename: str):
    """
    Serve an uploaded file publicly (no auth required).
    Used when MEDIA_STORAGE=db. In disk mode, Railway should serve
    MEDIA_ROOT via a CDN or nginx — this endpoint is the fallback.
    """
    # Sanitise
    filename = filename.lstrip("/")
    if ".." in filename:
        raise HTTPException(400, "Invalid path")

    # Try disk first
    disk_path = MEDIA_ROOT / filename
    if disk_path.exists() and disk_path.is_file():
        mime, _ = mimetypes.guess_type(str(disk_path))
        return Response(
            content=disk_path.read_bytes(),
            media_type=mime or "application/octet-stream",
            headers={"Cache-Control": "public, max-age=31536000"},
        )

    # Try DB (db mode or disk file missing)
    await _ensure_table()
    try:
        row = await database.fetch_one(
            "SELECT data, mime_type FROM media_files WHERE filename = :fn",
            {"fn": filename}
        )
        if row and row["data"]:
            content = base64.b64decode(row["data"])
            return Response(
                content=content,
                media_type=row["mime_type"] or "application/octet-stream",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as e:
        print(f"[MEDIA] Serve DB error: {e}", flush=True)

    raise HTTPException(404, "File not found")
