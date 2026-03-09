
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.config import settings
import asyncpg

router = APIRouter(prefix="/blog", tags=["blog"])

async def get_db():
    return await asyncpg.create_pool(settings.DATABASE_URL)

@router.get("/posts")
async def get_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = 0,
    category: Optional[str] = None,
    status: str = "published"
):
    pool = await get_db()
    async with pool.acquire() as conn:
        query = """
            SELECT id, title, slug, excerpt, category, featured_image, 
                   created_at, updated_at, author_id, views, is_premium
            FROM blog_posts 
            WHERE status = $1
        """
        params = [status]

        if category:
            query += " AND category = $2"
            params.append(category)

        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2)
        params.extend([limit, offset])

        posts = await conn.fetch(query, *params)
        return {"posts": [dict(p) for p in posts], "count": len(posts)}

@router.get("/posts/{slug}")
async def get_post(slug: str):
    pool = await get_db()
    async with pool.acquire() as conn:
        post = await conn.fetchrow("""
            SELECT * FROM blog_posts WHERE slug = $1
        """, slug)

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Increment views
        await conn.execute("UPDATE blog_posts SET views = views + 1 WHERE id = $1", post["id"])

        return dict(post)
