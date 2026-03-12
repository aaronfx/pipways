"""
Course and education content management.
"""
from fastapi import APIRouter, Depends
from backend.security import get_current_user
from backend.database import database

router = APIRouter()

@router.get("/list")
async def list_courses(current_user = Depends(get_current_user)):
    """List available courses."""
    return {"courses": [], "module": "courses"}

@router.get("/{course_id}")
async def get_course(course_id: int, current_user = Depends(get_current_user)):
    """Get specific course details."""
    return {"course_id": course_id, "title": "Sample Course"}
