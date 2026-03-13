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
                       created_at, updated_at, featured, read_time
                FROM blog_posts 
                WHERE status = 'published' AND category = :category
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            params = {"category": category, "limit": limit, "offset": offset}
        else:
            query = """
                SELECT id, title, slug, excerpt, content, category,
                       created_at, updated_at, featured, read_time
                FROM blog_posts 
                WHERE status = 'published'
                ORDER BY featured DESC, created_at DESC
                LIMIT :limit OFFSET :offset
            """
            params = {"limit": limit, "offset": offset}
            
        rows = await database.fetch_all(query, params)
        
        posts = []
        for row in rows:
            posts.append({
                "id": row["id"],
                "title": row["title"],
                "slug": row["slug"],
                "excerpt": row["excerpt"] or row["content"][:150] + "...",
                "content": row["content"],
                "category": row["category"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "featured": row.get("featured", False),
                "read_time": row.get("read_time", "5 min")
            })
            
        return posts
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch blog posts: {e}", flush=True)
        raise HTTPException(500, "Failed to load blog posts")

@router.get("/posts/{slug}")
async def get_post(slug: str, current_user = Depends(get_current_user)):
    """Get single post by slug"""
    try:
        query = "SELECT * FROM blog_posts WHERE slug = :slug AND status = 'published'"
        post = await database.fetch_one(query, {"slug": slug})
        
        if not post:
            raise HTTPException(404, "Post not found")
            
        return dict(post)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")
