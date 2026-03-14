"""
Courses API - PRODUCTION READY
Returns real course data from database with graceful error handling
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from .database import database, courses_table
from .security import get_current_user

router = APIRouter()

@router.get("/list")
async def get_courses(current_user = Depends(get_current_user)):
    """
    Get all available courses with user's progress
    Returns empty array on error instead of 500
    """
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        
        # Query courses from database
        query = """
            SELECT c.id, c.title, c.description, c.level, c.lesson_count,
                   COALESCE(up.progress_percent, 0) as progress,
                   COALESCE(up.completed_lessons, 0) as completed_lessons
            FROM courses c
            LEFT JOIN user_progress up ON c.id = up.course_id 
                AND up.user_id = :user_id
            WHERE c.is_active = true
            ORDER BY c.created_at DESC
        """
        
        rows = await database.fetch_all(query, {"user_id": user_id})
        
        courses = []
        for row in rows:
            courses.append({
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "level": row["level"],
                "lesson_count": row["lesson_count"],
                "progress": row["progress"],
                "completed_lessons": row["completed_lessons"]
            })
        
        return courses
        
    except Exception as e:
        print(f"[COURSES ERROR] Failed to fetch courses: {e}", flush=True)
        # Return empty array instead of crashing
        return []

@router.get("/{course_id}")
async def get_course_detail(course_id: int, current_user = Depends(get_current_user)):
    """Get specific course details"""
    try:
        query = "SELECT * FROM courses WHERE id = :id AND is_active = true"
        course = await database.fetch_one(query, {"id": course_id})
        
        if not course:
            raise HTTPException(404, "Course not found")
            
        return dict(course)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[COURSE DETAIL ERROR] {e}", flush=True)
        raise HTTPException(500, f"Database error: {str(e)}")
