from fastapi import APIRouter, Form, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
import re
import uuid
import json
from datetime import datetime

from auth import get_current_user, get_current_admin
from database import get_db

router = APIRouter()

@router.get("/posts")
async def get_blog_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    tag: Optional[str] = None,
    status: Optional[str] = "published",
    search: Optional[str] = None,
    conn=Depends(get_db)
):
    """Get blog posts with filtering and pagination"""
    try:
        offset = (page - 1) * per_page
        params = []
        where_clauses = []

        if status:
            where_clauses.append(f"status = ${len(params)+1}")
            params.append(status)

        if category:
            where_clauses.append(f"category = ${len(params)+1}")
            params.append(category)

        if tag:
            where_clauses.append(f"${len(params)+1} = ANY(tags)")
            params.append(tag)

        if search:
            where_clauses.append(f"(title ILIKE ${len(params)+1} OR content ILIKE ${len(params)+1} OR excerpt ILIKE ${len(params)+1})")
            params.append(f"%{search}%")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        posts = await conn.fetch(f"""
            SELECT id, title, slug, excerpt, featured_image, category, tags,
                   meta_title, meta_description, published_at, view_count, created_at
            FROM blog_posts
            WHERE {where_sql}
            ORDER BY published_at DESC NULLS LAST
            LIMIT ${len(params)+1} OFFSET ${len(params)+2}
        """, *params, per_page, offset)

        count_result = await conn.fetchrow(f"""
            SELECT COUNT(*) as total FROM blog_posts WHERE {where_sql}
        """, *params[:-2] if len(params) > 2 else [])

        total = count_result['total'] if count_result else 0

        return {
            "posts": [dict(p) for p in posts],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/post/{slug}")
async def get_blog_post(slug: str, conn=Depends(get_db)):
    """Get single blog post by slug"""
    try:
        post = await conn.fetchrow("""
            SELECT * FROM blog_posts WHERE slug = $1 AND status = 'published'
        """, slug)

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Increment view count
        await conn.execute("""
            UPDATE blog_posts SET view_count = view_count + 1 WHERE id = $1
        """, post['id'])

        return dict(post)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_blog_categories(conn=Depends(get_db)):
    """Get all blog categories"""
    try:
        categories = await conn.fetch("SELECT * FROM blog_categories ORDER BY name")
        return [dict(c) for c in categories]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tags")
async def get_blog_tags(conn=Depends(get_db)):
    """Get all unique tags"""
    try:
        result = await conn.fetch("SELECT DISTINCT unnest(tags) as tag FROM blog_posts WHERE status = 'published'")
        return [r['tag'] for r in result if r['tag']]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@router.post("/posts", dependencies=[Depends(get_current_admin)])
async def create_blog_post(
    title: str = Form(...),
    content: str = Form(...),
    excerpt: Optional[str] = Form(None),
    featured_image: Optional[str] = Form(None),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    status: str = Form("draft"),
    current_user: str = Depends(get_current_admin),
    conn=Depends(get_db)
):
    """Create new blog post (admin only)"""
    try:
        # Create slug from title
        slug = re.sub(r[^\w\s-], '', title.lower()).strip()
        slug = re.sub(r[-\s]+, '-', slug)

        # Ensure unique slug
        existing = await conn.fetchrow("SELECT id FROM blog_posts WHERE slug = $1", slug)
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"

        # Process tags
        tag_list = [t.strip() for t in tags.split(',')] if tags else []

        # Auto-generate excerpt and meta if not provided
        if not excerpt:
            excerpt = content[:200] + "..." if len(content) > 200 else content
        if not meta_title:
            meta_title = title[:70]
        if not meta_description:
            meta_description = excerpt[:160]

        published_at = datetime.utcnow() if status == 'published' else None

        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

        post_id = await conn.fetchval("""
            INSERT INTO blog_posts 
            (title, slug, content, excerpt, featured_image, meta_title, meta_description,
             meta_keywords, author_id, category, tags, status, published_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
        """,
            title, slug, content, excerpt, featured_image, meta_title, meta_description,
            meta_keywords, user["id"], category, tag_list, status, published_at
        )

        return {"success": True, "post_id": post_id, "slug": slug}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/posts/{post_id}", dependencies=[Depends(get_current_admin)])
async def update_blog_post(
    post_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    excerpt: Optional[str] = Form(None),
    featured_image: Optional[str] = Form(None),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    conn=Depends(get_db)
):
    """Update blog post (admin only)"""
    try:
        updates = []
        params = []

        if title:
            updates.append(f"title = ${len(params)+1}")
            params.append(title)
            new_slug = re.sub(r[^\w\s-], '', title.lower()).strip()
            new_slug = re.sub(r[-\s]+, '-', new_slug)
            updates.append(f"slug = ${len(params)+1}")
            params.append(f"{new_slug}-{uuid.uuid4().hex[:8]}")
        if content:
            updates.append(f"content = ${len(params)+1}")
            params.append(content)
        if excerpt:
            updates.append(f"excerpt = ${len(params)+1}")
            params.append(excerpt)
        if featured_image:
            updates.append(f"featured_image = ${len(params)+1}")
            params.append(featured_image)
        if meta_title:
            updates.append(f"meta_title = ${len(params)+1}")
            params.append(meta_title)
        if meta_description:
            updates.append(f"meta_description = ${len(params)+1}")
            params.append(meta_description)
        if category:
            updates.append(f"category = ${len(params)+1}")
            params.append(category)
        if tags:
            updates.append(f"tags = ${len(params)+1}")
            params.append([t.strip() for t in tags.split(',')])
        if status:
            updates.append(f"status = ${len(params)+1}")
            params.append(status)
            if status == 'published':
                updates.append(f"published_at = ${len(params)+1}")
                params.append(datetime.utcnow())

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append(f"updated_at = ${len(params)+1}")
        params.append(datetime.utcnow())
        params.append(post_id)

        await conn.execute(f"""
            UPDATE blog_posts SET {', '.join(updates)} WHERE id = ${len(params)}
        """, *params)

        return {"success": True, "message": "Post updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/posts/{post_id}", dependencies=[Depends(get_current_admin)])
async def delete_blog_post(post_id: int, conn=Depends(get_db)):
    """Delete blog post (admin only)"""
    try:
        await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        return {"success": True, "message": "Post deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
