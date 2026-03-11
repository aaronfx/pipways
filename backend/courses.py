"""
Courses Routes
Fixed: Wrapped responses with modules
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from . import database
from .security import get_current_user, get_current_user_optional, get_admin_user
from .schemas import CourseCreate, CourseModuleCreate

router = APIRouter()

@router.get("")
async def get_courses(search: Optional[str] = None, level: Optional[str] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get all courses with wrapped response"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = "SELECT * FROM courses WHERE 1=1"
        params = []
        
        if level:
            query += f" AND level = ${len(params)+1}"
            params.append(level)
        
        if search:
            query += f" AND (title ILIKE ${len(params)+1} OR description ILIKE ${len(params)+1})"
            params.append(f"%{search}%")
        
        query += " ORDER BY created_at DESC"
        
        courses = await conn.fetch(query, *params)
        
        result = []
        for course in courses:
            course_dict = dict(course)
            modules = await conn.fetch(
                "SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order", 
                course['id']
            )
            course_dict['modules'] = [dict(m) for m in modules]
            result.append(course_dict)
        
        return {"courses": result}

@router.get("/{course_id}")
async def get_course(course_id: int, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get single course with modules"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        course_dict = dict(course)
        modules = await conn.fetch(
            "SELECT * FROM course_modules WHERE course_id = $1 ORDER BY sort_order", 
            course_id
        )
        course_dict['modules'] = [dict(m) for m in modules]
        
        return course_dict

@router.post("")
async def create_course(course: CourseCreate, current_user: dict = Depends(get_admin_user)):
    """Create new course (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            INSERT INTO courses (title, description, content, level, duration_hours, thumbnail, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
        """
        course_id = await conn.fetchval(
            query,
            course.title,
            course.description,
            course.content,
            course.level,
            course.duration_hours,
            course.thumbnail,
            course.is_premium,
            current_user['id']
        )
        
        return {"id": course_id, "message": "Course created successfully"}

@router.put("/{course_id}")
async def update_course(course_id: int, course: CourseCreate, current_user: dict = Depends(get_admin_user)):
    """Update course (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            UPDATE courses 
            SET title = $1, description = $2, content = $3, level = $4, 
                duration_hours = $5, thumbnail = $6, is_premium = $7, updated_at = CURRENT_TIMESTAMP
            WHERE id = $8
        """
        await conn.execute(
            query,
            course.title,
            course.description,
            course.content,
            course.level,
            course.duration_hours,
            course.thumbnail,
            course.is_premium,
            course_id
        )
        
        return {"message": "Course updated successfully"}

@router.delete("/{course_id}")
async def delete_course(course_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete course (admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        return {"message": "Course deleted successfully"}

@router.post("/{course_id}/modules")
async def add_module(course_id: int, module: CourseModuleCreate, current_user: dict = Depends(get_admin_user)):
    """Add module to course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            INSERT INTO course_modules (course_id, title, content, video_url, is_premium, sort_order)
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id
        """
        module_id = await conn.fetchval(
            query,
            course_id,
            module.title,
            module.content,
            module.video_url,
            module.is_premium,
            module.sort_order
        )
        
        return {"id": module_id, "message": "Module added successfully"}

@router.put("/{course_id}/modules/{module_id}")
async def update_module(course_id: int, module_id: int, module: CourseModuleCreate, current_user: dict = Depends(get_admin_user)):
    """Update course module"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            UPDATE course_modules 
            SET title = $1, content = $2, video_url = $3, is_premium = $4, sort_order = $5
            WHERE id = $6 AND course_id = $7
        """
        await conn.execute(
            query,
            module.title,
            module.content,
            module.video_url,
            module.is_premium,
            module.sort_order,
            module_id,
            course_id
        )
        
        return {"message": "Module updated successfully"}

@router.delete("/{course_id}/modules/{module_id}")
async def delete_module(course_id: int, module_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete course module"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM course_modules WHERE id = $1 AND course_id = $2", module_id, course_id)
        return {"message": "Module deleted successfully"}
