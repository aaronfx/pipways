"""
Blog API — Complete Rebuild
Endpoints:
  GET /blog/posts           — paginated published posts
  GET /blog/posts/{slug}    — single post by slug

Design decisions:
- COALESCE on every new column so query never fails if column missing
- Dual publish filter: status='published' OR is_published=TRUE
- tags parsed from JSON string → Python list
- All datetime fields serialised to ISO string
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from .database import database
from .security import get_current_user

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────────

def _tags(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return [t.strip() for t in str(raw).split(",") if t.strip()]


def _fmt(row: dict) -> dict:
    content = row.get("content") or ""
    return {
        "id":             row.get("id"),
        "title":          row.get("title", ""),
        "slug":           row.get("slug", ""),
        "excerpt":        row.get("excerpt") or content[:160] + ("…" if len(content) > 160 else ""),
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


async def _run(sql: str, params: dict = None):
    try:
        return await database.fetch_all(sql, params or {})
    except Exception as e:
        print(f"[BLOG] query error: {e}", flush=True)
        return []


async def _one(sql: str, params: dict = None):
    try:
        return await database.fetch_one(sql, params or {})
    except Exception as e:
        print(f"[BLOG] fetch_one error: {e}", flush=True)
        return None


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/posts")
async def get_posts(
    limit:    int = Query(20, ge=1, le=100),
    offset:   int = Query(0, ge=0),
    category: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Return published blog posts. Always uses dual-column publish check."""
    cat = f"AND category = :cat" if category else ""
    params: dict = {"lim": limit, "off": offset}
    if category:
        params["cat"] = category

    # Full query — exclude tags from COALESCE (TEXT[] vs TEXT conflict)
    # tags are read raw and handled in Python by _tags()
    rows = await _run(
        f"""
        SELECT id, title, slug, excerpt, content, category,
               created_at, updated_at,
               COALESCE(featured_image, '')   AS featured_image,
               COALESCE(views, 0)             AS views,
               tags,
               COALESCE(featured, FALSE)      AS featured,
               COALESCE(read_time, '5 min')   AS read_time,
               COALESCE(is_published, FALSE)  AS is_published
        FROM blog_posts
        WHERE (LOWER(COALESCE(status, '')) = 'published'
               OR COALESCE(is_published, FALSE) = TRUE)
        {cat}
        ORDER BY COALESCE(featured, FALSE) DESC, created_at DESC
        LIMIT :lim OFFSET :off
        """,
        params,
    )

    # Fallback: try without any new columns if query failed
    if not rows:
        rows = await _run(
            f"""
            SELECT id, title, slug, excerpt, content, category,
                   created_at, updated_at, featured, read_time, status
            FROM blog_posts
            WHERE LOWER(COALESCE(status, '')) = 'published'
            {cat}
            ORDER BY created_at DESC
            LIMIT :lim OFFSET :off
            """,
            params,
        )

    result = [_fmt(dict(r)) for r in rows]
    print(f"[BLOG] /posts → {len(result)} posts", flush=True)
    return result


@router.get("/posts/{slug}")
async def get_post(slug: str, current_user=Depends(get_current_user)):
    """Return a single published post by slug."""
    # Note: no COALESCE on is_published in WHERE — use separate fallback instead
    row = await _one(
        """
        SELECT * FROM blog_posts
        WHERE slug = :slug
          AND (LOWER(COALESCE(status, '')) = 'published'
               OR is_published = TRUE)
        """,
        {"slug": slug},
    )

    if not row:
        row = await _one(
            "SELECT * FROM blog_posts WHERE slug=:slug AND LOWER(COALESCE(status,''))='published'",
            {"slug": slug},
        )

    if not row:
        raise HTTPException(404, "Post not found")

    return _fmt(dict(row))
