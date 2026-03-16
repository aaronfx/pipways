"""
Blog API - PRODUCTION READY
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from .database import database, blog_posts
from .security import get_current_user

router = APIRouter()

@router.get("/posts")
async def get_posts(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Get blog posts with pagination
    PRODUCTION: Real database queries
    """
    try:
        if category:
            query = """
                SELECT id, title, slug, excerpt, content, category,
                       COALESCE(featured_image, '') as featured_image,
                       COALESCE(views, 0) as views,
                       COALESCE(tags, '[]') as tags,
                       created_at, updated_at,
                       COALESCE(featured, false) as featured,
                       COALESCE(read_time, '5 min') as read_time,
                       COALESCE(is_published, false) as is_published,
                       COALESCE(status, 'published') as status
                FROM blog_posts
                WHERE (status = 'published' OR COALESCE(is_published, false) = TRUE)
                AND category = :category
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            params = {"category": category, "limit": limit, "offset": offset}
        else:
            query = """
                SELECT id, title, slug, excerpt, content, category,
                       COALESCE(featured_image, '') as featured_image,
                       COALESCE(views, 0) as views,
                       COALESCE(tags, '[]') as tags,
                       created_at, updated_at,
                       COALESCE(featured, false) as featured,
                       COALESCE(read_time, '5 min') as read_time,
                       COALESCE(is_published, false) as is_published,
                       COALESCE(status, 'published') as status
                FROM blog_posts
                WHERE (status = 'published' OR COALESCE(is_published, false) = TRUE)
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            params = {"limit": limit, "offset": offset}

        rows = await database.fetch_all(query, params)

    except Exception:
        # Fallback: columns not yet migrated — use only guaranteed original columns
        if category:
            query = """
                SELECT id, title, slug, excerpt, content, category,
                       created_at, updated_at, featured, read_time, status
                FROM blog_posts
                WHERE status = 'published' AND category = :category
                ORDER BY created_at DESC LIMIT :limit OFFSET :offset
            """
            params = {"category": category, "limit": limit, "offset": offset}
        else:
            query = """
                SELECT id, title, slug, excerpt, content, category,
                       created_at, updated_at, featured, read_time, status
                FROM blog_posts
                WHERE status = 'published'
                ORDER BY created_at DESC LIMIT :limit OFFSET :offset
            """
            params = {"limit": limit, "offset": offset}
        rows = await database.fetch_all(query, params)

        posts = []
        for row in rows:
            # Parse tags from JSON string or return empty list
            tags_raw = row.get("tags") or "[]"
            try:
                import json
                tags = json.loads(tags_raw) if isinstance(tags_raw, str) else (tags_raw or [])
            except Exception:
                tags = []

            posts.append({
                "id": row["id"],
                "title": row["title"],
                "slug": row["slug"],
                "excerpt": row.get("excerpt") or (row["content"][:150] + "..." if row.get("content") else ""),
                "content": row["content"],
                "category": row["category"],
                "featured_image": row.get("featured_image", ""),
                "views": row.get("views", 0),
                "tags": tags,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "featured": row.get("featured", False),
                "read_time": row.get("read_time", "5 min"),
                "is_published": bool(row.get("is_published", False)),
            })

        return posts
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch blog posts: {e}", flush=True)
        raise HTTPException(500, "Failed to load blog posts")

@router.get("/posts/{slug}")
async def get_post(slug: str, current_user = Depends(get_current_user)):
    """Get single post by slug"""
    try:
    try:
        query = "SELECT * FROM blog_posts WHERE slug = :slug AND (status = 'published' OR COALESCE(is_published, false) = TRUE)"
        post = await database.fetch_one(query, {"slug": slug})
    except Exception:
        query = "SELECT * FROM blog_posts WHERE slug = :slug AND status = 'published'"
        post = await database.fetch_one(query, {"slug": slug})

        if not post:
            raise HTTPException(404, "Post not found")

        result = dict(post)
        # Normalise tags to a list
        import json
        tags_raw = result.get("tags", "[]") or "[]"
        try:
            result["tags"] = json.loads(tags_raw) if isinstance(tags_raw, str) else (tags_raw or [])
        except Exception:
            result["tags"] = []
        # Serialise datetime fields
        if result.get("created_at"):
            result["created_at"] = result["created_at"].isoformat()
        if result.get("updated_at"):
            result["updated_at"] = result["updated_at"].isoformat()

        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")
