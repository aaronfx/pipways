"""
Courses API - PRODUCTION READY
Returns real course data from database with graceful error handling
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from .database import database, courses_table
from .security import get_current_user, get_user_id

router = APIRouter()

@router.get("/list")
async def get_courses(current_user = Depends(get_current_user)):
    """
    Get all available courses with user's progress.
    FIXED: Filters by is_active OR is_published (CMS sets both, old data may only have one).
    FIXED: Safe SQLAlchemy Row access for user_id.
    """
    try:
        # Use shared helper — handles SQLAlchemy Row, dict, and ORM models
        user_id = get_user_id(current_user)

        # FIXED: Check BOTH is_active AND is_published so courses published via CMS
        # are visible regardless of which column was set.
        query = """
            SELECT c.id, c.title, c.description, c.level,
                   c.lesson_count, c.thumbnail_url, c.instructor,
                   COALESCE(up.progress_percent, 0) as progress,
                   COALESCE(up.completed_lessons, 0) as completed_lessons
            FROM courses c
            LEFT JOIN user_progress up ON c.id = up.course_id
                AND up.user_id = :user_id
            WHERE c.is_active = TRUE OR c.is_published = TRUE
            ORDER BY c.created_at DESC
        """

        rows = await database.fetch_all(query, {"user_id": user_id})

        courses = []
        for row in rows:
            courses.append({
                "id":                row["id"],
                "title":             row["title"],
                "description":       row["description"],
                "level":             row["level"],
                "lesson_count":      row["lesson_count"],
                "thumbnail_url":     row.get("thumbnail_url", ""),
                "instructor":        row.get("instructor", ""),
                "progress":          row["progress"],
                "completed_lessons": row["completed_lessons"],
            })

        return courses

    except Exception as e:
        print(f"[COURSES ERROR] Failed to fetch courses: {e}", flush=True)
        return []

@router.get("/{course_id}")
async def get_course_detail(course_id: int, current_user = Depends(get_current_user)):
    """Get specific course details"""
    try:
        query = "SELECT * FROM courses WHERE id = :id AND (is_active = TRUE OR is_published = TRUE)"
        course = await database.fetch_one(query, {"id": course_id})
        
        if not course:
            raise HTTPException(404, "Course not found")
            
        return dict(course)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[COURSE DETAIL ERROR] {e}", flush=True)
        raise HTTPException(500, f"Database error: {str(e)}")
