"""
Blog API — Bulletproof Rebuild
Endpoints:
  GET /blog/posts           — paginated published posts
  GET /blog/posts/{slug}    — single post by slug

Root cause of empty blog: `featured` and `read_time` columns did not exist
on the live DB. Any query referencing them fails silently → empty [].
Fix: 3-stage waterfall queries — full → partial → minimum.
database.py now adds the missing columns via migration.
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from .database import database
from .security import get_current_user

router = APIRouter()


def _tags(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return [t.strip() for t in str(raw).split(",") if t.strip()]


def _fmt(row: dict) -> dict:
    content = row.get("content") or ""
    excerpt = row.get("excerpt") or ""
    return {
        "id":             row.get("id"),
        "title":          row.get("title", ""),
        "slug":           row.get("slug", ""),
        "excerpt":        excerpt or (content[:160] + ("..." if len(content) > 160 else "")),
        "content":        content,
        "category":       row.get("category") or "General",
        "featured_image": row.get("featured_image") or "",
        "views":          row.get("views") or 0,
        "tags":           _tags(row.get("tags")),
        "featured":       bool(row.get("featured", False)),
        "read_time":      row.get("read_time") or "5 min",
        "is_published":   bool(row.get("is_published", False)),
        "created_at":     row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at":     row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


async def _fetch(sql: str, params: dict = None) -> list:
    try:
        rows = await database.fetch_all(sql, params or {})
        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        print(f"[BLOG] query failed: {e}", flush=True)
        return []


async def _fetch_one(sql: str, params: dict = None):
    try:
        row = await database.fetch_one(sql, params or {})
        return dict(row) if row else None
    except Exception as e:
        print(f"[BLOG] fetch_one failed: {e}", flush=True)
        return None


@router.get("/posts")
async def get_posts(
    limit:    int = Query(20, ge=1, le=100),
    offset:   int = Query(0, ge=0),
    category: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    cat_sql = "AND category = :cat" if category else ""
    params: dict = {"lim": limit, "off": offset}
    if category:
        params["cat"] = category

    # Stage 1: all columns (works after migration adds featured + read_time)
    rows = await _fetch(
        f"""
        SELECT id, title, slug, excerpt, content, category,
               created_at, updated_at, status,
               featured_image, views, tags,
               featured, read_time, is_published
        FROM blog_posts
        WHERE (LOWER(status) = 'published' OR is_published = TRUE)
        {cat_sql}
        ORDER BY featured DESC NULLS LAST, created_at DESC
        LIMIT :lim OFFSET :off
        """, params,
    )

    # Stage 2: without featured + read_time (before migration runs)
    if not rows:
        rows = await _fetch(
            f"""
            SELECT id, title, slug, excerpt, content, category,
                   created_at, updated_at, status,
                   featured_image, views, tags, is_published
            FROM blog_posts
            WHERE (LOWER(status) = 'published' OR is_published = TRUE)
            {cat_sql}
            ORDER BY created_at DESC
            LIMIT :lim OFFSET :off
            """, params,
        )

    # Stage 3: absolute minimum — original schema only
    if not rows:
        rows = await _fetch(
            f"""
            SELECT id, title, slug, excerpt, content, category,
                   created_at, updated_at, status
            FROM blog_posts
            WHERE LOWER(status) = 'published'
            {cat_sql}
            ORDER BY created_at DESC
            LIMIT :lim OFFSET :off
            """, params,
        )

    result = [_fmt(r) for r in rows]
    print(f"[BLOG] /posts -> {len(result)} posts", flush=True)
    return result


@router.get("/posts/{slug}")
async def get_post(slug: str, current_user=Depends(get_current_user)):
    # Try with is_published
    row = await _fetch_one(
        "SELECT * FROM blog_posts WHERE slug = :slug AND (LOWER(status) = 'published' OR is_published = TRUE)",
        {"slug": slug},
    )
    # Fallback without is_published
    if not row:
        row = await _fetch_one(
            "SELECT * FROM blog_posts WHERE slug = :slug AND LOWER(status) = 'published'",
            {"slug": slug},
        )
    if not row:
        raise HTTPException(404, "Post not found")
    return _fmt(row)
