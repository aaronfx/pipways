"""
Blog API - PRODUCTION READY
Resilient to missing columns via COALESCE + fallback queries.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from .database import database
from .security import get_current_user

router = APIRouter()


def _parse_tags(raw) -> list:
    if not raw:
        return []
    try:
        return json.loads(raw) if isinstance(raw, str) else (raw or [])
    except Exception:
        return []


def _fmt_row(row: dict) -> dict:
    return {
        "id":             row.get("id"),
        "title":          row.get("title", ""),
        "slug":           row.get("slug", ""),
        "excerpt":        row.get("excerpt") or (row.get("content", "")[:150] + "..."),
        "content":        row.get("content", ""),
        "category":       row.get("category", "General"),
        "featured_image": row.get("featured_image", ""),
        "views":          row.get("views", 0),
        "tags":           _parse_tags(row.get("tags")),
        "created_at":     row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at":     row["updated_at"].isoformat() if row.get("updated_at") else None,
        "featured":       bool(row.get("featured", False)),
        "read_time":      row.get("read_time", "5 min"),
        "is_published":   bool(row.get("is_published", False)),
    }


@router.get("/posts")
async def get_posts(
    limit:    int = Query(10, ge=1, le=100),
    offset:   int = Query(0, ge=0),
    category: Optional[str] = None,
    current_user = Depends(get_current_user),
):
    cat_clause = "AND category = :category" if category else ""
    params: dict = {"limit": limit, "offset": offset}
    if category:
        params["category"] = category

    # Try rich query with new columns first
    try:
        q = f"""
            SELECT id, title, slug, excerpt, content, category,
                   COALESCE(featured_image, '') AS featured_image,
                   COALESCE(views, 0)           AS views,
                   COALESCE(tags, '[]')         AS tags,
                   created_at, updated_at,
                   COALESCE(featured, FALSE)    AS featured,
                   COALESCE(read_time, '5 min') AS read_time,
                   COALESCE(is_published, FALSE) AS is_published
            FROM blog_posts
            WHERE (status = 'published' OR COALESCE(is_published, FALSE) = TRUE)
            {cat_clause}
            ORDER BY COALESCE(featured, FALSE) DESC, created_at DESC
            LIMIT :limit OFFSET :offset
        """
        rows = await database.fetch_all(q, params)
    except Exception:
        # Fallback — old schema without new columns
        q = f"""
            SELECT id, title, slug, excerpt, content, category,
                   created_at, updated_at, featured, read_time, status
            FROM blog_posts
            WHERE status = 'published' {cat_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        rows = await database.fetch_all(q, params)

    return [_fmt_row(dict(r)) for r in rows]


@router.get("/posts/{slug}")
async def get_post(slug: str, current_user = Depends(get_current_user)):
    """Get a single published post by slug."""
    try:
        q = "SELECT * FROM blog_posts WHERE slug = :slug AND (status = 'published' OR COALESCE(is_published, FALSE) = TRUE)"
        row = await database.fetch_one(q, {"slug": slug})
    except Exception:
        q = "SELECT * FROM blog_posts WHERE slug = :slug AND status = 'published'"
        row = await database.fetch_one(q, {"slug": slug})

    if not row:
        raise HTTPException(404, "Post not found")

    return _fmt_row(dict(row))
