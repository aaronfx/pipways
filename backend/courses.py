"""
Courses Routes
Endpoints: /api/courses/*
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from .database import db_pool
from .security import get_current_user, get_admin_user
from .schemas import CourseCreate, CourseUpdate, ModuleCreate, QuizCreate, QuizAttempt

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.post("")
async def create_course(
    course: CourseCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new course (admin only)"""
    async with db_pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (
                title, description, content, is_premium, level, duration_hours, thumbnail, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            course.title, course.description, course.content, course.is_premium,
            course.level, course.duration_hours, course.thumbnail, current_user["id"]
        )
        return {"id": course_id, "message": "Course created"}

@router.get("")
async def list_courses(
    level: Optional[str] = Query(None, regex="^(beginner|intermediate|advanced)$"),
    is_premium: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """List courses"""
    async with db_pool.acquire() as conn:
        where_clauses = ["1=1"]
        params = []
        param_idx = 1

        if level:
            where_clauses.append(f"level = ${param_idx}")
            params.append(level)
            param_idx += 1
        if is_premium is not None:
            where_clauses.append(f"is_premium = ${param_idx}")
            params.append(is_premium)
            param_idx += 1

        # Check premium access
        if current_user.get("subscription_tier") not in ["vip", "premium"]:
            where_clauses.append("is_premium = FALSE")

        where_sql = " AND ".join(where_clauses)

        rows = await conn.fetch(f"""
            SELECT * FROM courses 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx}
        """, *params, limit)

        return [dict(row) for row in rows]

@router.get("/{course_id}")
async def get_course(
    course_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get course details with modules"""
    async with db_pool.acquire() as conn:
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Check premium
        if course["is_premium"] and current_user.get("subscription_tier") not in ["vip", "premium"]:
            raise HTTPException(status_code=403, detail="Premium subscription required")

        modules = await conn.fetch("""
            SELECT * FROM course_modules 
            WHERE course_id = $1 
            ORDER BY sort_order
        """, course_id)

        result = dict(course)
        result["modules"] = [dict(m) for m in modules]
        return result

# Module routes
@router.post("/{course_id}/modules")
async def create_module(
    course_id: int,
    module: ModuleCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Add module to course"""
    async with db_pool.acquire() as conn:
        module_id = await conn.fetchval("""
            INSERT INTO course_modules (course_id, title, content, video_url, sort_order, is_premium)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, course_id, module.title, module.content, module.video_url, module.sort_order, module.is_premium)
        return {"id": module_id, "message": "Module added"}

# Quiz routes
@router.post("/{course_id}/quizzes")
async def create_quiz(
    course_id: int,
    quiz: QuizCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create quiz for course"""
    async with db_pool.acquire() as conn:
        quiz_id = await conn.fetchval("""
            INSERT INTO course_quizzes (course_id, title, description, passing_score, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, course_id, quiz.title, quiz.description, quiz.passing_score, current_user["id"])
        return {"id": quiz_id, "message": "Quiz created"}

@router.post("/{course_id}/quizzes/{quiz_id}/attempt")
async def submit_quiz_attempt(
    course_id: int,
    quiz_id: int,
    attempt: QuizAttempt,
    current_user: dict = Depends(get_current_user)
):
    """Submit quiz attempt"""
    async with db_pool.acquire() as conn:
        # Simple scoring logic - in production this would be more sophisticated
        score = 0
        max_score = len(attempt.answers) if attempt.answers else 0
        passed = score >= 70  # Placeholder logic

        attempt_id = await conn.fetchval("""
            INSERT INTO quiz_attempts (quiz_id, user_id, answers, score, max_score, percentage, passed)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, quiz_id, current_user["id"], attempt.answers, score, max_score, 
            (score/max_score*100) if max_score > 0 else 0, passed)

        return {"attempt_id": attempt_id, "score": score, "passed": passed}
