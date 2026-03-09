
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.dependencies import require_admin, generate_slug
from app.models.schemas import BlogPostCreate, CourseCreate, WebinarCreate, SignalCreate
from app.config import settings
import asyncpg

router = APIRouter(prefix="/admin", tags=["admin"])

async def get_db():
    return await asyncpg.create_pool(settings.DATABASE_URL)

@router.get("/stats")
async def get_stats(current_user: dict = Depends(require_admin)):
    pool = await get_db()
    async with pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        premium_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE subscription_tier != 'free'")
        active_signals = await conn.fetchval("SELECT COUNT(*) FROM signals WHERE status = 'active'")
        blog_posts = await conn.fetchval("SELECT COUNT(*) FROM blog_posts")
        courses = await conn.fetchval("SELECT COUNT(*) FROM courses")
        webinars = await conn.fetchval("SELECT COUNT(*) FROM webinars")

        return {
            "total_users": total_users,
            "premium_users": premium_users,
            "active_signals": active_signals,
            "content_stats": {
                "blog_posts": blog_posts,
                "courses": courses,
                "webinars": webinars
            }
        }

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(require_admin)
):
    pool = await get_db()
    async with pool.acquire() as conn:
        offset = (page - 1) * limit
        users = await conn.fetch("""
            SELECT id, email, full_name, role, subscription_tier, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT $1 OFFSET $2
        """, limit, offset)

        total = await conn.fetchval("SELECT COUNT(*) FROM users")

        return {
            "users": [dict(u) for u in users],
            "page": page,
            "pages": (total + limit - 1) // limit,
            "total": total
        }

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"message": "User deleted"}

@router.post("/blog")
async def create_blog_post(post: BlogPostCreate, current_user: dict = Depends(require_admin)):
    pool = await get_db()
    async with pool.acquire() as conn:
        slug = post.slug or generate_slug(post.title)

        # Check slug uniqueness
        existing = await conn.fetchval("SELECT id FROM blog_posts WHERE slug = $1", slug)
        if existing:
            slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        post_id = await conn.fetchval("""
            INSERT INTO blog_posts 
            (title, slug, content, excerpt, category, status, scheduled_at, 
             featured_image, meta_title, meta_description, tags, is_premium, author_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
        """, 
            post.title, slug, post.content, post.excerpt, post.category,
            post.status, post.scheduled_at, post.featured_image, post.meta_title,
            post.meta_description, post.tags, post.is_premium, current_user["id"]
        )

        return {"id": post_id, "slug": slug, "message": "Blog post created"}

@router.delete("/blog/{post_id}")
async def delete_blog_post(post_id: int, current_user: dict = Depends(require_admin)):
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        return {"message": "Post deleted"}

@router.post("/courses")
async def create_course(course: CourseCreate, current_user: dict = Depends(require_admin)):
    pool = await get_db()
    async with pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, content, level, duration_hours, 
                               thumbnail, is_premium, instructor_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
        """, course.title, course.description, course.content, course.level,
            course.duration_hours, course.thumbnail, course.is_premium, current_user["id"])

        # Insert modules
        for idx, module in enumerate(course.modules):
            await conn.execute("""
                INSERT INTO course_modules (course_id, title, content, video_url, 
                                          duration_minutes, sort_order)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, course_id, module.title, module.content, module.video_url,
                module.duration_minutes, idx)

        return {"id": course_id, "message": "Course created"}

@router.post("/webinars")
async def create_webinar(webinar: WebinarCreate, current_user: dict = Depends(require_admin)):
    pool = await get_db()
    async with pool.acquire() as conn:
        webinar_id = await conn.fetchval("""
            INSERT INTO webinars (title, description, scheduled_at, duration_minutes,
                                max_participants, meeting_link, is_premium, host_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
        """, webinar.title, webinar.description, webinar.scheduled_at,
            webinar.duration_minutes, webinar.max_participants, webinar.meeting_link,
            webinar.is_premium, current_user["id"])

        return {"id": webinar_id, "message": "Webinar created"}

@router.post("/signals")
async def create_signal(signal: SignalCreate, current_user: dict = Depends(require_admin)):
    pool = await get_db()
    async with pool.acquire() as conn:
        signal_id = await conn.fetchval("""
            INSERT INTO signals (pair, direction, entry_price, stop_loss, take_profit,
                               timeframe, analysis, is_premium, status, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', $9) RETURNING id
        """, signal.pair, signal.direction, signal.entry_price, signal.stop_loss,
            signal.take_profit, signal.timeframe, signal.analysis, signal.is_premium,
            current_user["id"])

        return {"id": signal_id, "message": "Signal created"}
