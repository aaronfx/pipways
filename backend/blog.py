"""
Blog Routes
Handles blog posts and articles
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from . import database
from .security import get_current_user_optional, get_admin_user
from .schemas import BlogPostCreate

router = APIRouter()

@router.get("")
async def get_posts(status: Optional[str] = "published", category: Optional[str] = None, 
                   search: Optional[str] = None, limit: int = 50, 
                   current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get blog posts"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = "SELECT * FROM blog_posts WHERE 1=1"
        params = []
        
        if status:
            query += f" AND status = ${len(params)+1}"
            params.append(status)
        
        if category:
            query += f" AND category = ${len(params)+1}"
            params.append(category)
        
        if search:
            query += f" AND (title ILIKE ${len(params)+1} OR content ILIKE ${len(params)+1})"
            params.append(f"%{search}%")
        
        query += " ORDER BY created_at DESC"
        query += f" LIMIT ${len(params)+1}"
        params.append(limit)
        
        posts = await conn.fetch(query, *params)
        
        # FIXED: Return wrapped response
        return {"posts": [dict(p) for p in posts]}

@router.get("/{post_id}")
async def get_post(post_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        post = await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return dict(post)

@router.post("")
async def create_post(post: BlogPostCreate, current_user: dict = Depends(get_admin_user)):
    """Create new post (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Generate slug from title
        slug = post.title.lower().replace(" ", "-")[:50]
        
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (title, content, excerpt, category, featured_image, is_premium, status, slug, author_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id
        """, post.title, post.content, post.excerpt, post.category, 
            post.featured_image, post.is_premium, post.status, slug, current_user['id'])
        
        return {"id": post_id, "message": "Post created successfully"}

@router.put("/{post_id}")
async def update_post(post_id: int, post: BlogPostCreate, current_user: dict = Depends(get_admin_user)):
    """Update post (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE blog_posts 
            SET title = $1, content = $2, excerpt = $3, category = $4, 
                featured_image = $5, is_premium = $6, status = $7, updated_at = CURRENT_TIMESTAMP
            WHERE id = $8
        """, post.title, post.content, post.excerpt, post.category,
            post.featured_image, post.is_premium, post.status, post_id)
        
        return {"message": "Post updated successfully"}

@router.delete("/{post_id}")
async def delete_post(post_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete post (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        return {"message": "Post deleted successfully"}
