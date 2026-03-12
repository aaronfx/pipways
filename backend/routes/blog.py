"""
Blog Routes - SEO-Optimized Content Management
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime
import json

from .. import database
from ..schemas import BlogPostCreate, BlogPostUpdate, BlogPostResponse, SEOMetadata
from ..security import get_current_user, get_admin_user, get_current_user_optional

router = APIRouter()

@router.get("/")
async def get_blog_posts(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    featured: bool = False,
    page: int = 1,
    limit: int = 10
):
    """Get blog posts with filtering"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    offset = (page - 1) * limit
    
    async with database.db_pool.acquire() as conn:
        query = """
            SELECT bp.*, u.full_name as author_name,
                   (SELECT COUNT(*) FROM blog_comments WHERE post_id = bp.id) as comments_count
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE bp.status = 'published'
        """
        params = []
        
        if category:
            query += f" AND bp.category = ${len(params)+1}"
            params.append(category)
        
        if tag:
            query += f" AND ${len(params)+1} = ANY(bp.tags)"
            params.append(tag)
        
        if featured:
            query += " AND bp.is_featured = TRUE"
        
        if search:
            query += f" AND (bp.title ILIKE ${len(params)+1} OR bp.content ILIKE ${len(params)+1})"
            params.append(f"%{search}%")
        
        count_query = query.replace("SELECT bp.*, u.full_name as author_name", "SELECT COUNT(*)")
        total = await conn.fetchval(count_query, *params)
        
        query += f" ORDER BY bp.published_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        params.extend([limit, offset])
        
        posts = await conn.fetch(query, *params)
        
        return {
            "posts": [dict(p) for p in posts],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

@router.get("/{slug}")
async def get_blog_post(
    slug: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get single blog post by slug"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        post = await conn.fetchrow("""
            SELECT bp.*, u.full_name as author_name
            FROM blog_posts bp
            LEFT JOIN users u ON bp.author_id = u.id
            WHERE bp.slug = $1 AND bp.status = 'published'
        """, slug)
        
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        await conn.execute("""
            UPDATE blog_posts SET views = views + 1 WHERE id = $1
        """, post['id'])
        
        comments = await conn.fetch("""
            SELECT bc.*, u.full_name as author_name
            FROM blog_comments bc
            LEFT JOIN users u ON bc.user_id = u.id
            WHERE bc.post_id = $1 AND bc.is_approved = TRUE
            ORDER BY bc.created_at DESC
        """, post['id'])
        
        post_dict = dict(post)
        post_dict['comments'] = [dict(c) for c in comments]
        
        return post_dict

@router.post("/", response_model=BlogPostResponse)
async def create_blog_post(
    post: BlogPostCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new blog post (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        slug = post.slug or post.title.lower().replace(" ", "-")
        
        existing = await conn.fetchval("SELECT id FROM blog_posts WHERE slug = $1", slug)
        if existing:
            slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (
                title, slug, content, excerpt, featured_image,
                category, tags, meta_title, meta_description, focus_keyword,
                author_id, status, is_featured, views, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 0, CURRENT_TIMESTAMP)
            RETURNING id
        """,
            post.title, slug, post.content, post.excerpt, post.featured_image,
            post.category, post.tags, post.meta_title or post.title,
            post.meta_description or post.excerpt, post.focus_keyword,
            current_user['id'], post.status or 'draft', post.is_featured or False
        )
        
        return await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)

@router.put("/{post_id}")
async def update_blog_post(
    post_id: int,
    post_update: BlogPostUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update blog post (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        updates = []
        values = []
        
        updateable = ['title', 'slug', 'content', 'excerpt', 'featured_image',
                     'category', 'tags', 'meta_title', 'meta_description', 
                     'focus_keyword', 'status', 'is_featured']
        
        for field in updateable:
            value = getattr(post_update, field, None)
            if value is not None:
                updates.append(f"{field} = ${len(values)+1}")
                values.append(value)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(post_id)
        
        query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ${len(values)} RETURNING *"
        row = await conn.fetchrow(query, *values)
        
        return dict(row)

@router.delete("/{post_id}")
async def delete_blog_post(
    post_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete blog post (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        return {"message": "Blog post deleted successfully"}

@router.post("/{post_id}/comments")
async def add_comment(
    post_id: int,
    content: str,
    current_user: dict = Depends(get_current_user)
):
    """Add comment to blog post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        comment_id = await conn.fetchval("""
            INSERT INTO blog_comments (post_id, user_id, content, is_approved, created_at)
            VALUES ($1, $2, $3, FALSE, CURRENT_TIMESTAMP)
            RETURNING id
        """, post_id, current_user['id'], content)
        
        return {"id": comment_id, "message": "Comment submitted for moderation"}
