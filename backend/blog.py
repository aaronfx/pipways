"""
Blog Routes
Endpoints: /api/blog/*
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from .database import db_pool
from .security import get_current_user, get_admin_user, get_current_user_optional
from .schemas import BlogPostCreate, BlogPostUpdate

router = APIRouter(prefix="/api/blog", tags=["blog"])

@router.post("")
async def create_post(
    post: BlogPostCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create blog post (admin only)"""
    async with db_pool.acquire() as conn:
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (
                title, content, excerpt, author_id, is_premium, status, scheduled_at,
                meta_title, meta_description, slug, featured_image, tags, category
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
        """,
            post.title, post.content, post.excerpt or post.content[:200], current_user["id"],
            post.is_premium, post.status, post.scheduled_at, post.meta_title,
            post.meta_description, post.slug, post.featured_image, post.tags or [], post.category
        )
        return {"id": post_id, "message": "Post created"}

@router.get("")
async def list_posts(
    status: str = Query("published", regex="^(draft|published|scheduled)$"),
    category: Optional[str] = None,
    tag: Optional[str] = None,
    is_premium: Optional[bool] = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """List blog posts"""
    async with db_pool.acquire() as conn:
        where_clauses = ["status = $1"]
        params = [status]
        param_idx = 2

        if category:
            where_clauses.append(f"category = ${param_idx}")
            params.append(category)
            param_idx += 1
        if tag:
            where_clauses.append(f"${param_idx} = ANY(tags)")
            params.append(tag)
            param_idx += 1
        if is_premium is not None:
            where_clauses.append(f"is_premium = ${param_idx}")
            params.append(is_premium)
            param_idx += 1

        # Check premium access
        if not current_user or current_user.get("subscription_tier") not in ["vip", "premium"]:
            where_clauses.append("is_premium = FALSE")

        where_sql = " AND ".join(where_clauses)

        rows = await conn.fetch(f"""
            SELECT 
                id, title, excerpt, featured_image, category, tags, is_premium,
                created_at, updated_at, author_id, status, slug
            FROM blog_posts 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """, *params, limit, offset)

        return [dict(row) for row in rows]

@router.get("/{post_id}")
async def get_post(
    post_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get single blog post"""
    async with db_pool.acquire() as conn:
        post = await conn.fetchrow("""
            SELECT * FROM blog_posts WHERE id = $1
        """, post_id)

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check premium access
        if post["is_premium"] and (not current_user or current_user.get("subscription_tier") not in ["vip", "premium"]):
            raise HTTPException(status_code=403, detail="Premium subscription required")

        return dict(post)

@router.put("/{post_id}")
async def update_post(
    post_id: int,
    post: BlogPostUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update blog post (admin only)"""
    async with db_pool.acquire() as conn:
        # Build dynamic update
        updates = []
        params = []

        fields = [
            ("title", post.title),
            ("content", post.content),
            ("excerpt", post.excerpt),
            ("is_premium", post.is_premium),
            ("status", post.status),
            ("scheduled_at", post.scheduled_at),
            ("meta_title", post.meta_title),
            ("meta_description", post.meta_description),
            ("slug", post.slug),
            ("featured_image", post.featured_image),
            ("tags", post.tags),
            ("category", post.category)
        ]

        for field, value in fields:
            if value is not None:
                updates.append(f"{field} = ${len(params) + 1}")
                params.append(value)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        params.append(post_id)

        sql = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ${len(params)} RETURNING id"
        updated = await conn.fetchrow(sql, *params)

        if not updated:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post updated"}

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete blog post (admin only)"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        if deleted == "DELETE 0":
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted"}
