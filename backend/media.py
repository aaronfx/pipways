"""
backend/media.py — Cloudinary-backed media library for Gopipways CMS.

WHY CLOUDINARY: Railway containers are ephemeral — local files are wiped on
every deployment. Cloudinary stores files on a persistent CDN so images
survive deploys forever.

Required Railway env vars (add in Railway → Variables):
    CLOUDINARY_CLOUD_NAME   your cloud name from cloudinary.com dashboard
    CLOUDINARY_API_KEY      your API key
    CLOUDINARY_API_SECRET   your API secret

Free tier: 25 GB storage + 25 GB bandwidth/month — more than enough.

Fallback (no Cloudinary): set MEDIA_STORAGE=db to store files as base64
in PostgreSQL instead (works, but slow for large images and bloats the DB).

Endpoints (mounted by main.py under /cms/media):
    POST   /cms/media/upload          — upload a file (admin only)
    GET    /cms/media                 — list uploaded files (admin only)
    GET    /cms/media?folder=blog     — list by folder
    DELETE /cms/media?filename=...    — delete a file (admin only)
    GET    /cms/media/serve/{path}    — serve file publicly (fallback / db mode)
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

MEDIA_STORAGE     = os.getenv("MEDIA_STORAGE", "db").lower()
MEDIA_MAX_MB      = int(os.getenv("MEDIA_MAX_MB", "20"))
MAX_BYTES         = MEDIA_MAX_MB * 1024 * 1024

# Cloudinary (primary — persistent across deployments)
CLOUDINARY_CLOUD  = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_KEY    = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_FOLDER = "gopipways"

# Disk fallback (ephemeral on Railway — only use for local dev)
MEDIA_ROOT        = Path(os.getenv("MEDIA_ROOT", "/app/uploads"))
MEDIA_BASE_URL    = os.getenv(
    "MEDIA_BASE_URL",
    "https://www.gopipways.com/cms/media/serve"
)

# Allowed MIME types → Cloudinary resource_type
ALLOWED_TYPES: dict[str, str] = {
    "image/jpeg":      "image",
    "image/png":       "image",
    "image/webp":      "image",
    "image/gif":       "image",
    "image/svg+xml":   "image",
    "video/mp4":       "video",
    "video/webm":      "video",
    "application/pdf": "raw",
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


# ── Cloudinary helpers ────────────────────────────────────────────────────────

def _cloudinary_configured() -> bool:
    return bool(CLOUDINARY_CLOUD and CLOUDINARY_KEY and CLOUDINARY_SECRET)


def _get_cloudinary():
    """Import and configure cloudinary lazily."""
    try:
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD,
            api_key=CLOUDINARY_KEY,
            api_secret=CLOUDINARY_SECRET,
            secure=True,
        )
        return cloudinary
    except ImportError:
        raise HTTPException(
            500,
            "cloudinary package not installed. Run: pip install cloudinary"
        )


def _safe_stem(original: str) -> str:
    stem = Path(original).stem[:40]
    return re.sub(r"[^a-z0-9_-]", "_", stem.lower())


async def _cloudinary_upload(data: bytes, original: str, content_type: str,
                              folder: str, user_id: int) -> dict:
    cl = _get_cloudinary()
    resource_type = ALLOWED_TYPES.get(content_type, "image")
    stem    = _safe_stem(original)
    uid     = uuid.uuid4().hex[:8]
    pub_id  = f"{CLOUDINARY_FOLDER}/{folder}/{stem}_{uid}"

    result = cl.uploader.upload(
        data,
        public_id=pub_id,
        resource_type=resource_type,
        overwrite=False,
    )
    url      = result["secure_url"]
    filename = result["public_id"]   # used as the delete key

    # Log in DB for easy listing (no blob stored)
    await _ensure_table()
    try:
        await database.execute(
            """
            INSERT INTO media_files
                (filename, original, mime_type, folder, size_bytes, url, uploaded_by)
            VALUES (:fn, :orig, :mime, :folder, :size, :url, :uid)
            ON CONFLICT (filename) DO UPDATE
                SET url=EXCLUDED.url, size_bytes=EXCLUDED.size_bytes
            """,
            {"fn": filename, "orig": original, "mime": content_type,
             "folder": folder, "size": len(data), "url": url, "uid": user_id}
        )
    except Exception as db_err:
        print(f"[MEDIA] DB log warning (non-fatal): {db_err}", flush=True)

    return {
        "success":       True,
        "url":           url,
        "filename":      filename,
        "original_name": original,
        "folder":        folder,
        "size":          len(data),
        "mime_type":     content_type,
    }


async def _cloudinary_list(folder: Optional[str]) -> list:
    cl = _get_cloudinary()
    prefix = f"{CLOUDINARY_FOLDER}/{folder}" if folder else CLOUDINARY_FOLDER
    items  = []
    for rtype in ("image", "video", "raw"):
        try:
            res = cl.api.resources(
                type="upload",
                prefix=prefix,
                max_results=200,
                resource_type=rtype,
            )
            for r in res.get("resources", []):
                items.append({
                    "url":           r["secure_url"],
                    "filename":      r["public_id"],
                    "original_name": r["public_id"].split("/")[-1],
                    "folder":        folder or "general",
                    "resource_type": rtype,
                    "size":          r.get("bytes", 0),
                    "created_at":    r.get("created_at"),
                })
        except Exception as e:
            print(f"[MEDIA] Cloudinary list {rtype} warning: {e}", flush=True)
    return items


async def _cloudinary_delete(public_id: str) -> None:
    cl = _get_cloudinary()
    deleted = False
    for rtype in ("image", "video", "raw"):
        try:
            result = cl.uploader.destroy(public_id, resource_type=rtype)
            if result.get("result") == "ok":
                deleted = True
                break
        except Exception:
            continue
    if not deleted:
        raise HTTPException(404, "File not found or already deleted")
    # Remove from DB log
    try:
        await database.execute(
            "DELETE FROM media_files WHERE filename = :fn", {"fn": public_id}
        )
    except Exception:
        pass


# ── Disk / DB helpers (fallback) ──────────────────────────────────────────────

def _public_url(filename: str) -> str:
    return f"{MEDIA_BASE_URL.rstrip('/')}/{filename}"

def _safe_filename(original: str, folder: str) -> str:
    ext  = Path(original).suffix.lower()
    stem = _safe_stem(original)
    uid  = uuid.uuid4().hex[:8]
    return f"{folder}/{stem}_{uid}{ext}"

async def _db_upload(filename: str, mime: str, data: bytes, folder: str,
                     original: str, size: int, url: str, user_id: int) -> None:
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


# ── POST /cms/media/upload ────────────────────────────────────────────────────

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin access required")

    await _ensure_table()

    # Validate MIME
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type == "application/octet-stream" or not content_type:
        guessed, _ = mimetypes.guess_type(file.filename or "")
        content_type = guessed or "application/octet-stream"

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            400,
            f"File type '{content_type}' not allowed. Allowed: {', '.join(ALLOWED_TYPES)}"
        )

    data = await file.read()
    if not data:
        raise HTTPException(400, "Uploaded file is empty")
    if len(data) > MAX_BYTES:
        raise HTTPException(
            400,
            f"File too large ({len(data)//1024//1024} MB). Maximum: {MEDIA_MAX_MB} MB"
        )

    original = file.filename or "upload"
    folder   = ALLOWED_TYPES[content_type]   # images / video / raw → used as subfolder

    # Determine user_id safely across dict and Row objects
    user_id = 0
    try:
        user_id = current_user.get("id", 0) if hasattr(current_user, "get") else current_user["id"]
    except Exception:
        pass

    # ── Route to storage backend ──────────────────────────────────────────
    if MEDIA_STORAGE == "cloudinary" and _cloudinary_configured():
        try:
            result = await _cloudinary_upload(data, original, content_type, folder, user_id)
            print(f"[MEDIA] ✅ Cloudinary upload: {original} → {result['filename']}", flush=True)
            return result
        except HTTPException:
            raise
        except Exception as e:
            print(f"[MEDIA] Cloudinary upload failed: {e} — falling back to DB", flush=True)
            # Fall through to DB storage

    if MEDIA_STORAGE == "db" or (MEDIA_STORAGE == "cloudinary" and not _cloudinary_configured()):
        filename = _safe_filename(original, folder)
        url      = _public_url(filename)
        await _db_upload(filename, content_type, data, folder, original, len(data), url, user_id)
        print(f"[MEDIA] ✅ DB upload: {original} → {filename}", flush=True)
        return {
            "success": True, "url": url, "filename": filename,
            "original_name": original, "folder": folder,
            "size": len(data), "mime_type": content_type,
        }

    # Disk mode (local dev only — ephemeral on Railway)
    filename = _safe_filename(original, folder)
    url      = _public_url(filename)
    dest     = MEDIA_ROOT / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
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
             "folder": folder, "size": len(data), "url": url, "uid": user_id}
        )
    except Exception as db_err:
        print(f"[MEDIA] DB log warning: {db_err}", flush=True)
    print(f"[MEDIA] ✅ Disk upload: {original} → {filename}", flush=True)
    return {
        "success": True, "url": url, "filename": filename,
        "original_name": original, "folder": folder,
        "size": len(data), "mime_type": content_type,
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

    if MEDIA_STORAGE == "cloudinary" and _cloudinary_configured():
        items = await _cloudinary_list(folder)
        return {"files": items, "count": len(items), "folder": folder or "all"}

    # DB / disk fallback — read from media_files table
    try:
        sql    = "SELECT filename, original, mime_type, folder, size_bytes, url, created_at FROM media_files"
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

    # Also scan disk in disk mode
    if MEDIA_STORAGE == "disk":
        scan_root = MEDIA_ROOT / (folder if folder and folder != "all" else "")
        if scan_root.exists():
            db_names = {i["filename"] for i in items}
            for p in scan_root.rglob("*"):
                if p.is_file():
                    rel = str(p.relative_to(MEDIA_ROOT))
                    if rel not in db_names:
                        mime, _ = mimetypes.guess_type(str(p))
                        items.append({
                            "filename": rel, "original_name": p.name,
                            "mime_type": mime or "application/octet-stream",
                            "folder": p.parent.name, "size": p.stat().st_size,
                            "url": _public_url(rel), "created_at": None,
                        })

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

    if MEDIA_STORAGE == "cloudinary" and _cloudinary_configured():
        await _cloudinary_delete(filename)
        return {"success": True, "deleted": filename}

    # DB / disk fallback
    deleted = False
    if MEDIA_STORAGE == "disk":
        target = MEDIA_ROOT / filename
        if target.exists() and target.is_file():
            target.unlink()
            deleted = True
    try:
        await database.execute(
            "DELETE FROM media_files WHERE filename = :fn", {"fn": filename}
        )
        deleted = True
    except Exception as e:
        print(f"[MEDIA] DB delete warning: {e}", flush=True)

    if not deleted:
        raise HTTPException(404, f"File not found: {filename}")

    return {"success": True, "deleted": filename}


# ── GET /cms/media/serve/{filename:path} ──────────────────────────────────────

@router.get("/serve/{filename:path}")
async def serve_media(filename: str):
    """
    Serve a file publicly. Used in db mode or as fallback when
    Cloudinary is the primary store and you need to serve a DB-stored file.
    In Cloudinary mode, the CDN URL is returned directly — this endpoint
    is a fallback for files stored in the DB.
    """
    filename = filename.lstrip("/")
    if ".." in filename:
        raise HTTPException(400, "Invalid path")

    # Try disk
    disk_path = MEDIA_ROOT / filename
    if disk_path.exists() and disk_path.is_file():
        mime, _ = mimetypes.guess_type(str(disk_path))
        return Response(
            content=disk_path.read_bytes(),
            media_type=mime or "application/octet-stream",
            headers={"Cache-Control": "public, max-age=31536000"},
        )

    # Try DB
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
