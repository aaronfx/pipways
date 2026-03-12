from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, insert, update, delete, desc, func
from pydantic import BaseModel
import re
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import database, blog_posts, users
from .security import get_current_user, get_current_admin

router = APIRouter(prefix="/blog", tags=["blog"])
limiter = Limiter(key_func=get_remote_address)

def generate_slug(title: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug

class BlogPostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    category: str
    tags: List[str] = []
    featured_image: Optional[str] = None

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    featured_image: Optional[str] = None
    is_published: Optional[bool] = None

class BlogPostResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: str
    featured_image: Optional[str]
    category: str
    tags: List[str]
    author_id: int
    is_published: bool
    views: int
    created_at: datetime
    updated_at: datetime

@router.get("/", response_model=List[BlogPostResponse])
@limiter.limit("30/minute")
async def get_posts(
    request: Request,
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_published: bool = Query(True),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    query = select(blog_posts).order_by(desc(blog_posts.c.created_at))

    if is_published:
        query = query.where(blog_posts.c.is_published == True)
    if category:
        query = query.where(blog_posts.c.category == category)
    if tag:
        query = query.where(blog_posts.c.tags.contains([tag]))

    query = query.limit(limit).offset(offset)
    results = await database.fetch_all(query)
    return [dict(row) for row in results]

@router.get("/slug/{slug}", response_model=BlogPostResponse)
async def get_post_by_slug(slug: str):
    query = select(blog_posts).where(blog_posts.c.slug == slug)
    result = await database.fetch_one(query)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")

    query = update(blog_posts).where(blog_posts.c.id == result["id"]).values(
        views=result["views"] + 1
    )
    await database.execute(query)

    return dict(result)

@router.get("/{post_id}", response_model=BlogPostResponse)
async def get_post(post_id: int):
    query = select(blog_posts).where(blog_posts.c.id == post_id)
    result = await database.fetch_one(query)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return dict(result)

@router.post("/", response_model=BlogPostResponse)
async def create_post(
    post_data: BlogPostCreate,
    current_user: dict = Depends(get_current_admin)
):
    slug = generate_slug(post_data.title)

    query = select(blog_posts).where(blog_posts.c.slug == slug)
    existing = await database.fetch_one(query)
    if existing:
        slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    excerpt = post_data.excerpt or post_data.content[:200] + "..."

    query = insert(blog_posts).values(
        title=post_data.title,
        slug=slug,
        content=post_data.content,
        excerpt=excerpt,
        featured_image=post_data.featured_image,
        category=post_data.category,
        tags=post_data.tags,
        author_id=current_user["id"],
        is_published=False,
        views=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    post_id = await database.execute(query)

    query = select(blog_posts).where(blog_posts.c.id == post_id)
    result = await database.fetch_one(query)
    return dict(result)

@router.put("/{post_id}", response_model=BlogPostResponse)
async def update_post(
    post_id: int,
    post_update: BlogPostUpdate,
    current_user: dict = Depends(get_current_admin)
):
    query = select(blog_posts).where(blog_posts.c.id == post_id)
    existing = await database.fetch_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")

    update_data = post_update.dict(exclude_unset=True)

    if "title" in update_data:
        new_slug = generate_slug(update_data["title"])
        query = select(blog_posts).where(
            (blog_posts.c.slug == new_slug) & (blog_posts.c.id != post_id)
        )
        slug_exists = await database.fetch_one(query)
        if slug_exists:
            new_slug = f"{new_slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        update_data["slug"] = new_slug

    update_data["updated_at"] = datetime.utcnow()

    query = update(blog_posts).where(blog_posts.c.id == post_id).values(**update_data)
    await database.execute(query)

    query = select(blog_posts).where(blog_posts.c.id == post_id)
    result = await database.fetch_one(query)
    return dict(result)

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: dict = Depends(get_current_admin)
):
    query = delete(blog_posts).where(blog_posts.c.id == post_id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}
