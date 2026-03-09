
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user
from app.config import settings
import asyncpg

router = APIRouter(prefix="/courses", tags=["courses"])

async def get_db():
    return await asyncpg.create_pool(settings.DATABASE_URL)

@router.get("/")
async def get_courses(limit: int = 20, current_user: dict = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        courses = await conn.fetch("""
            SELECT c.*, u.full_name as instructor_name,
                   (SELECT COUNT(*) FROM course_modules WHERE course_id = c.id) as module_count
            FROM courses c
            JOIN users u ON c.instructor_id = u.id
            WHERE c.is_premium = false OR $1 = true
            ORDER BY c.created_at DESC
            LIMIT $2
        """, current_user.get("subscription_tier") in ["premium", "pro"], limit)

        return {"courses": [dict(c) for c in courses]}

@router.get("/{course_id}")
async def get_course(course_id: int, current_user: dict = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Check access
        if course["is_premium"] and current_user.get("subscription_tier") == "free":
            raise HTTPException(status_code=403, detail="Premium content")

        modules = await conn.fetch("""
            SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order
        """, course_id)

        result = dict(course)
        result["modules"] = [dict(m) for m in modules]
        return result
