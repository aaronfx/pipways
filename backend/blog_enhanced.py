from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy import select, insert, update, delete, desc, func, ARRAY
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
import re

from .database import (
    database, blog_posts, blog_seo_metadata, content_upgrades, 
    email_captures, content_calendar, users
)
from .security import get_current_user, get_current_admin
from .ai_services import generate_content

router = APIRouter(prefix="/blog", tags=["blog_enhanced"])

class SEOMetadata(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[List[str]] = None
    featured: Optional[bool] = False

class ContentUpgradeCreate(BaseModel):
    upgrade_type: str
    title: str
    require_email: bool = True

class EmailCaptureRequest(BaseModel):
    email: str
    upgrade_id: int

class ContentCalendarItem(BaseModel):
    planned_title: str
    category: str
    target_keyword: str
    planned_publish_date: date
    assigned_to: int

@router.post("/{post_id}/seo")
async def update_seo_metadata(
    post_id: int,
    seo_data: SEOMetadata,
    current_user: dict = Depends(get_current_admin)
):
    query = select(blog_seo_metadata).where(blog_seo_metadata.c.post_id == post_id)
    existing = await database.fetch_one(query)

    if existing:
        query = update(blog_seo_metadata).where(
            blog_seo_metadata.c.post_id == post_id
        ).values(
            meta_title=seo_data.meta_title,
            meta_description=seo_data.meta_description,
            keywords=seo_data.keywords,
            featured=seo_data.featured
        )
    else:
        query = insert(blog_seo_metadata).values(
            post_id=post_id,
            meta_title=seo_data.meta_title,
            meta_description=seo_data.meta_description,
            keywords=seo_data.keywords,
            featured=seo_data.featured
        )

    await database.execute(query)
    return {"status": "updated"}

@router.post("/{post_id}/auto-seo")
async def auto_generate_seo(
    post_id: int,
    current_user: dict = Depends(get_current_admin)
):
    query = select(blog_posts).where(blog_posts.c.id == post_id)
    post = await database.fetch_one(query)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    prompt = f"Generate SEO meta title (max 60 chars) and meta description (max 155 chars) for: {post['title']}"
    result = await generate_content(prompt)

    meta_title = post['title'][:60]
    meta_description = post['excerpt'][:155] if post['excerpt'] else post['content'][:155]
    keywords = []

    lines = result.split("\n")
    for line in lines:
        if "Title:" in line or "title:" in line:
            meta_title = line.split(":", 1)[1].strip()[:70]
        if "Description:" in line or "description:" in line:
            meta_description = line.split(":", 1)[1].strip()[:160]
        if "Keywords:" in line:
            kw_text = line.split(":", 1)[1].strip()
            keywords = [k.strip() for k in kw_text.split(",")]

    word_count = len(post['content'].split())
    reading_time = max(1, word_count // 200)

    query = insert(blog_seo_metadata).values(
        post_id=post_id,
        meta_title=meta_title,
        meta_description=meta_description,
        keywords=keywords,
        reading_time_minutes=reading_time,
        canonical_url=f"/blog/{post['slug']}"
    )

    try:
        await database.execute(query)
    except:
        query = update(blog_seo_metadata).where(
            blog_seo_metadata.c.post_id == post_id
        ).values(
            meta_title=meta_title,
            meta_description=meta_description,
            keywords=keywords,
            reading_time_minutes=reading_time
        )
        await database.execute(query)

    return {
        "meta_title": meta_title,
        "meta_description": meta_description,
        "keywords": keywords,
        "reading_time": reading_time
    }

@router.get("/{post_id}/related")
async def get_related_posts(post_id: int, limit: int = 3):
    query = select(blog_posts).where(blog_posts.c.id == post_id)
    post = await database.fetch_one(query)

    if not post or not post['tags']:
        return []

    tag_list = post['tags']
    query = select(blog_posts, func.count().label("common_tags")).where(
        (blog_posts.c.id != post_id) &
        (blog_posts.c.is_published == True) &
        (blog_posts.c.tags.overlap(tag_list))
    ).group_by(blog_posts.c.id).order_by(desc("common_tags")).limit(limit)

    results = await database.fetch_all(query)
    return [dict(r) for r in results]

@router.post("/{post_id}/upgrades")
async def create_content_upgrade(
    post_id: int,
    upgrade_data: ContentUpgradeCreate,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_admin)
):
    filename = f"upgrade_{post_id}_{file.filename}"
    file_path = f"uploads/{filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    query = insert(content_upgrades).values(
        post_id=post_id,
        upgrade_type=upgrade_data.upgrade_type,
        title=upgrade_data.title,
        file_path=file_path,
        require_email=upgrade_data.require_email,
        download_count=0
    )
    upgrade_id = await database.execute(query)

    return {
        "id": upgrade_id,
        "title": upgrade_data.title,
        "file_url": f"/uploads/{filename}"
    }

@router.post("/capture-email")
async def capture_email(data: EmailCaptureRequest):
    query = select(content_upgrades).where(content_upgrades.c.id == data.upgrade_id)
    upgrade = await database.fetch_one(query)

    if not upgrade:
        raise HTTPException(status_code=404, detail="Upgrade not found")

    query = insert(email_captures).values(
        email=data.email,
        post_id=upgrade["post_id"],
        upgrade_id=data.upgrade_id,
        captured_at=datetime.utcnow()
    )
    await database.execute(query)

    query = update(content_upgrades).where(
        content_upgrades.c.id == data.upgrade_id
    ).values(download_count=content_upgrades.c.download_count + 1)
    await database.execute(query)

    return {
        "download_url": f"/uploads/{upgrade['file_path'].split('/')[-1]}",
        "message": "Email captured successfully"
    }

@router.post("/calendar")
async def add_to_calendar(
    item: ContentCalendarItem,
    current_user: dict = Depends(get_current_admin)
):
    query = insert(content_calendar).values(
        planned_title=item.planned_title,
        category=item.category,
        target_keyword=item.target_keyword,
        assigned_to=item.assigned_to,
        planned_publish_date=item.planned_publish_date,
        status="planned"
    )
    calendar_id = await database.execute(query)
    return {"id": calendar_id, "status": "added"}

@router.get("/calendar")
async def get_calendar(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = select(content_calendar, users.c.username).join(
        users, content_calendar.c.assigned_to == users.c.id
    )

    if status:
        query = query.where(content_calendar.c.status == status)

    query = query.order_by(content_calendar.c.planned_publish_date)
    results = await database.fetch_all(query)
    return [dict(r) for r in results]

@router.get("/{post_id}/analytics")
async def get_post_analytics(
    post_id: int,
    current_user: dict = Depends(get_current_admin)
):
    query = select(blog_posts).where(blog_posts.c.id == post_id)
    post = await database.fetch_one(query)

    query = select(blog_seo_metadata).where(blog_seo_metadata.c.post_id == post_id)
    seo = await database.fetch_one(query)

    query = select(func.count()).where(email_captures.c.post_id == post_id)
    captures = await database.fetch_val(query)

    return {
        "post_id": post_id,
        "title": post["title"] if post else None,
        "views": post["views"] if post else 0,
        "unique_views": seo["unique_view_count"] if seo else 0,
        "avg_time_on_page": seo["avg_time_on_page"] if seo else 0,
        "email_captures": captures,
        "reading_time": seo["reading_time_minutes"] if seo else 0,
        "newsletter_sent": seo["newsletter_sent"] if seo else False,
        "featured": seo["featured"] if seo else False
    }
