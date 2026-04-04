"""
media_service.py — Cloudinary-backed media storage for Gopipways CMS
Replaces local filesystem uploads which are wiped on every Railway deployment.

Setup:
    1. pip install cloudinary
    2. Add to Railway env vars:
         CLOUDINARY_CLOUD_NAME=your_cloud_name
         CLOUDINARY_API_KEY=your_api_key
         CLOUDINARY_API_SECRET=your_api_secret
    3. Free tier: 25GB storage, 25GB bandwidth/month — plenty for CMS media
"""

import os
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException

# ── Configure Cloudinary from env vars ───────────────────────────────────────
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key    = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure     = True
)

# Allowed MIME types → Cloudinary resource type mapping
ALLOWED_TYPES = {
    "image/jpeg":      "image",
    "image/png":       "image",
    "image/webp":      "image",
    "image/gif":       "image",
    "image/svg+xml":   "image",
    "video/mp4":       "video",
    "video/webm":      "video",
    "application/pdf": "raw",
}

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def upload_media(file: UploadFile, folder: str = "general") -> dict:
    """
    Upload a file to Cloudinary under gopipways/{folder}/.
    Returns a dict with: url, filename, original_name, folder, resource_type, size
    """
    # Validate MIME type
    content_type = file.content_type or ""
    resource_type = ALLOWED_TYPES.get(content_type)
    if not resource_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: images, videos, PDFs."
        )

    # Read file content
    content = await file.read()

    # Validate size
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(content)//1024//1024}MB). Maximum: {MAX_FILE_SIZE_MB}MB."
        )

    # Build a stable public_id so the URL is predictable
    # Format: gopipways/{folder}/{original_stem}_{short_uuid}
    original_name = file.filename or "upload"
    stem = os.path.splitext(original_name)[0][:50]  # cap stem length
    short_id = uuid.uuid4().hex[:8]
    public_id = f"gopipways/{folder}/{stem}_{short_id}"

    # Upload to Cloudinary
    try:
        result = cloudinary.uploader.upload(
            content,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=False,
            # For PDFs: return the raw URL, not a preview
            format=None if resource_type != "raw" else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    return {
        "url":           result["secure_url"],
        "filename":      result["public_id"],          # used as the delete key
        "original_name": original_name,
        "folder":        folder,
        "resource_type": resource_type,
        "size":          result.get("bytes", len(content)),
        "width":         result.get("width"),
        "height":        result.get("height"),
    }


async def list_media(folder: str = None) -> list:
    """
    List all media files in gopipways/ or a specific subfolder.
    Returns a list of dicts compatible with the CMS media grid.
    """
    prefix = f"gopipways/{folder}" if folder else "gopipways"
    results = []

    try:
        # Fetch images
        img_res = cloudinary.api.resources(
            type="upload",
            prefix=prefix,
            max_results=200,
            resource_type="image"
        )
        results.extend(img_res.get("resources", []))

        # Fetch videos
        vid_res = cloudinary.api.resources(
            type="upload",
            prefix=prefix,
            max_results=200,
            resource_type="video"
        )
        results.extend(vid_res.get("resources", []))

        # Fetch raw (PDFs)
        raw_res = cloudinary.api.resources(
            type="upload",
            prefix=prefix,
            max_results=200,
            resource_type="raw"
        )
        results.extend(raw_res.get("resources", []))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list media: {str(e)}")

    # Normalise to the shape the CMS frontend expects
    return [
        {
            "url":           r["secure_url"],
            "filename":      r["public_id"],
            "original_name": r["public_id"].split("/")[-1],
            "folder":        folder or "general",
            "resource_type": r.get("resource_type", "image"),
            "size":          r.get("bytes", 0),
            "created_at":    r.get("created_at"),
        }
        for r in results
    ]


async def delete_media(public_id: str) -> dict:
    """
    Delete a file from Cloudinary by its public_id (the 'filename' field from upload/list).
    Tries all resource types since we don't know which type the file is.
    """
    deleted = False
    for resource_type in ("image", "video", "raw"):
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            if result.get("result") == "ok":
                deleted = True
                break
        except Exception:
            continue

    if not deleted:
        raise HTTPException(status_code=404, detail="File not found or already deleted.")

    return {"deleted": True, "filename": public_id}
