"""Enhanced Blog Routes with Media, SEO, and Multi-Image Support"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime
import re
import json

from . import database
from .security import get_current_user, get_current_user_optional, get_admin_user

router = APIRouter()

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:255]

def extract_images_from_content(content: str) -> List[str]:
    """Extract image URLs from markdown content"""
    import re
    pattern = r'!\[.*?\]\((.*?)\)'
    return re.findall(pattern, content)

@router.get("")
async def get_posts(
    status: Optional[str] = "published",
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get blog posts with filtering"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = "SELECT b.*, u.full_name as author_name FROM blog_posts b JOIN users u ON b.author_id = u.id WHERE 1=1"
        params = []
        
        # If not admin, only show published
        if not current_user or current_user.get('role') not in ['admin', 'moderator']:
            query += " AND b.status = 'published' AND (b.is_premium = FALSE OR EXISTS (SELECT 1 FROM users WHERE id = $1 AND subscription_tier = 'vip'))"
            params.append(current_user['id'] if current_user else 0)
        elif status:
            query += f" AND b.status = ${len(params)+1}"
            params.append(status)
        
        if category:
            query += f" AND b.category = ${len(params)+1}"
            params.append(category)
        
        if search:
            query += f" AND (b.title ILIKE ${len(params)+1} OR b.content ILIKE ${len(params)+1})"
            params.append(f"%{search}%")
        
        # Get total count
        count_query = query.replace("b.*, u.full_name as author_name", "COUNT(*)")
        total = await conn.fetchval(count_query, *params)
        
        # Add pagination
        query += f" ORDER BY b.created_at DESC OFFSET ${len(params)+1} LIMIT ${len(params)+2}"
        params.append((page - 1) * limit)
        params.append(limit)
        
        posts = await conn.fetch(query, *params)
        
        # Get media for each post
        result = []
        for post in posts:
            post_dict = dict(post)
            media = await conn.fetch("SELECT * FROM blog_media WHERE post_id = $1 ORDER BY sort_order", post['id'])
            post_dict['media'] = [dict(m) for m in media]
            
            # Get SEO data
            seo = await conn.fetchrow("SELECT * FROM blog_seo_data WHERE post_id = $1", post['id'])
            if seo:
                post_dict['seo'] = dict(seo)
            
            result.append(post_dict)
        
        return {
            "posts": result,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

@router.get("/{post_id}")
async def get_post(
    post_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get single post with related posts"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        post = await conn.fetchrow("""
            SELECT b.*, u.full_name as author_name 
            FROM blog_posts b 
            JOIN users u ON b.author_id = u.id 
            WHERE b.id = $1
        """, post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check access
        if post['status'] != 'published' or post['is_premium']:
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            if current_user['role'] not in ['admin', 'moderator'] and current_user['subscription_tier'] != 'vip':
                raise HTTPException(status_code=403, detail="VIP access required")
        
        post_dict = dict(post)
        
        # Increment views
        await conn.execute("UPDATE blog_posts SET views = views + 1 WHERE id = $1", post_id)
        post_dict['views'] += 1
        
        # Get media
        media = await conn.fetch("SELECT * FROM blog_media WHERE post_id = $1 ORDER BY sort_order", post_id)
        post_dict['media'] = [dict(m) for m in media]
        
        # Get SEO
        seo = await conn.fetchrow("SELECT * FROM blog_seo_data WHERE post_id = $1", post_id)
        if seo:
            post_dict['seo'] = dict(seo)
        
        # Get related posts (same category)
        related = await conn.fetch("""
            SELECT id, title, featured_image, created_at FROM blog_posts 
            WHERE category = $1 AND id != $2 AND status = 'published'
            ORDER BY created_at DESC LIMIT 3
        """, post['category'], post_id)
        post_dict['related_posts'] = [dict(r) for r in related]
        
        return post_dict

@router.post("")
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    excerpt: Optional[str] = Form(None),
    category: str = Form("General"),
    status: str = Form("draft"),
    is_premium: bool = Form(False),
    featured_image: Optional[str] = Form(None),
    seo_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    focus_keyword: Optional[str] = Form(None),
    current_user: dict = Depends(get_admin_user)
):
    """Create blog post with SEO data"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Generate excerpt if not provided
        if not excerpt:
            excerpt = content[:200] + "..." if len(content) > 200 else content
        
        # Generate slug
        slug = generate_slug(title)
        
        # Check slug uniqueness
        existing = await conn.fetchval("SELECT id FROM blog_seo_data WHERE slug = $1", slug)
        if existing:
            slug += f"-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        post_id = await conn.fetchval("""
            INSERT INTO blog_posts (title, content, excerpt, category, author_id, status, is_premium, featured_image)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, title, content, excerpt, category, current_user['id'], status, is_premium, featured_image)
        
        # Create SEO entry
        await conn.execute("""
            INSERT INTO blog_seo_data (post_id, seo_title, meta_description, focus_keyword, slug)
            VALUES ($1, $2, $3, $4, $5)
        """, post_id, seo_title or title, meta_description or excerpt[:160], focus_keyword, slug)
        
        # Auto-extract and save images from content
        images = extract_images_from_content(content)
        for idx, img_url in enumerate(images):
            await conn.execute("""
                INSERT INTO blog_media (post_id, url, filename, alt_text, sort_order)
                VALUES ($1, $2, $3, $4, $5)
            """, post_id, img_url, img_url.split('/')[-1], title, idx)
        
        return {"id": post_id, "slug": slug, "message": "Post created successfully"}

@router.put("/{post_id}")
async def update_post(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: Optional[str] = Form(None),
    category: str = Form("General"),
    status: str = Form("draft"),
    is_premium: bool = Form(False),
    featured_image: Optional[str] = Form(None),
    seo_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    focus_keyword: Optional[str] = Form(None),
    current_user: dict = Depends(get_admin_user)
):
    """Update blog post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        if not excerpt:
            excerpt = content[:200] + "..." if len(content) > 200 else content
        
        await conn.execute("""
            UPDATE blog_posts 
            SET title = $1, content = $2, excerpt = $3, category = $4, 
                status = $5, is_premium = $6, featured_image = $7, updated_at = CURRENT_TIMESTAMP
            WHERE id = $8
        """, title, content, excerpt, category, status, is_premium, featured_image, post_id)
        
        # Update SEO
        await conn.execute("""
            UPDATE blog_seo_data 
            SET seo_title = $1, meta_description = $2, focus_keyword = $3, updated_at = CURRENT_TIMESTAMP
            WHERE post_id = $4
        """, seo_title or title, meta_description or excerpt[:160], focus_keyword, post_id)
        
        return {"message": "Post updated successfully"}

@router.delete("/{post_id}")
async def delete_post(post_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete blog post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        return {"message": "Post deleted successfully"}

@router.post("/{post_id}/media")
async def add_media(
    post_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    alt_text: Optional[str] = Form(None),
    current_user: dict = Depends(get_admin_user)
):
    """Add media to blog post"""
    # Save file logic here (implement your file storage)
    # For now, placeholder
    file_url = f"/uploads/{file.filename}"
    
    async with database.db_pool.acquire() as conn:
        max_order = await conn.fetchval("""
            SELECT COALESCE(MAX(sort_order), 0) FROM blog_media WHERE post_id = $1
        """, post_id)
        
        media_id = await conn.fetchval("""
            INSERT INTO blog_media (post_id, filename, url, caption, alt_text, sort_order)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, post_id, file.filename, file_url, caption, alt_text, max_order + 1)
        
        return {"id": media_id, "url": file_url, "message": "Media added successfully"}

@router.get("/by-slug/{slug}")
async def get_post_by_slug(slug: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get post by SEO slug"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        seo_data = await conn.fetchrow("SELECT post_id FROM blog_seo_data WHERE slug = $1", slug)
        if not seo_data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Reuse get_post logic
        return await get_post(seo_data['post_id'], current_user)
