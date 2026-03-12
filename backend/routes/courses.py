"""
Course Routes - Learning Management System
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime

# ABSOLUTE IMPORTS (no dots)
import database
from schemas import (
    CourseCreate, CourseUpdate, CourseResponse,
    LessonCreate, LessonUpdate, QuizCreate, QuizSubmit,
    EnrollmentResponse, ProgressResponse, QuestionCreate, AnswerCreate
)
from security import get_current_user, get_admin_user, get_current_user_optional

router = APIRouter()

@router.get("/")
async def get_courses(
    status: Optional[str] = "published",
    category: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get courses list"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            SELECT c.*, u.full_name as instructor_name,
                   (SELECT COUNT(*) FROM lessons WHERE course_id = c.id) as lessons_count
            FROM courses c
            LEFT JOIN users u ON c.instructor_id = u.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += f" AND c.status = ${len(params)+1}"
            params.append(status)
        if category:
            query += f" AND c.category = ${len(params)+1}"
            params.append(category)
        
        # Hide draft courses from non-admins
        if not current_user or current_user.get('role') not in ['admin', 'moderator']:
            query += " AND c.status = 'published'"
        
        query += " ORDER BY c.created_at DESC"
        
        courses = await conn.fetch(query, *params)
        return [dict(c) for c in courses]

@router.get("/{course_id}")
async def get_course(
    course_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get single course with lessons"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course = await conn.fetchrow("""
            SELECT c.*, u.full_name as instructor_name
            FROM courses c
            LEFT JOIN users u ON c.instructor_id = u.id
            WHERE c.id = $1
        """, course_id)
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check if user is enrolled
        is_enrolled = False
        progress = 0
        if current_user:
            enrollment = await conn.fetchrow("""
                SELECT * FROM enrollments WHERE user_id = $1 AND course_id = $2
            """, current_user['id'], course_id)
            if enrollment:
                is_enrolled = True
                progress = enrollment['progress_percent']
        
        # Get lessons
        lessons = await conn.fetch("""
            SELECT * FROM lessons WHERE course_id = $1 ORDER BY order_index ASC
        """, course_id)
        
        course_dict = dict(course)
        course_dict['lessons'] = [dict(l) for l in lessons]
        course_dict['is_enrolled'] = is_enrolled
        course_dict['progress_percent'] = progress
        
        return course_dict

@router.post("/")
async def create_course(
    course: CourseCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create new course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (
                title, description, short_description, category, level,
                duration_minutes, instructor_id, thumbnail_url, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP)
            RETURNING id
        """,
            course.title,
            course.description,
            course.short_description,
            course.category,
            course.level,
            course.duration_minutes,
            current_user['id'],
            course.thumbnail_url,
            course.status or 'draft'
        )
        
        return await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)

@router.put("/{course_id}")
async def update_course(
    course_id: int,
    course_update: CourseUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Course not found")
        
        updates = []
        values = []
        
        updateable = ['title', 'description', 'short_description', 'category', 
                     'level', 'duration_minutes', 'thumbnail_url', 'status']
        
        for field in updateable:
            value = getattr(course_update, field, None)
            if value is not None:
                updates.append(f"{field} = ${len(values)+1}")
                values.append(value)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(course_id)
        
        query = f"UPDATE courses SET {', '.join(updates)} WHERE id = ${len(values)} RETURNING *"
        row = await conn.fetchrow(query, *values)
        
        return dict(row)

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Delete course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Course not found")
        
        return {"message": "Course deleted successfully"}

# Lessons
@router.post("/{course_id}/lessons")
async def create_lesson(
    course_id: int,
    lesson: LessonCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Add lesson to course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Verify course exists
        course = await conn.fetchval("SELECT id FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        lesson_id = await conn.fetchval("""
            INSERT INTO lessons (
                course_id, title, content, video_url, order_index, 
                duration_minutes, is_preview, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
            RETURNING id
        """,
            course_id,
            lesson.title,
            lesson.content,
            lesson.video_url,
            lesson.order_index,
            lesson.duration_minutes,
            lesson.is_preview or False
        )
        
        return await conn.fetchrow("SELECT * FROM lessons WHERE id = $1", lesson_id)

# Enrollment
@router.post("/{course_id}/enroll")
async def enroll_in_course(
    course_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Enroll current user in course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Check if already enrolled
        existing = await conn.fetchval("""
            SELECT id FROM enrollments WHERE user_id = $1 AND course_id = $2
        """, current_user['id'], course_id)
        
        if existing:
            return {"message": "Already enrolled", "enrollment_id": existing}
        
        # Create enrollment
        enrollment_id = await conn.fetchval("""
            INSERT INTO enrollments (user_id, course_id, progress_percent, enrolled_at)
            VALUES ($1, $2, 0, CURRENT_TIMESTAMP)
            RETURNING id
        """, current_user['id'], course_id)
        
        return {"message": "Enrolled successfully", "enrollment_id": enrollment_id}

# Quizzes
@router.post("/{course_id}/quizzes")
async def create_quiz(
    course_id: int,
    quiz: QuizCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create quiz for course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        quiz_id = await conn.fetchval("""
            INSERT INTO quizzes (course_id, lesson_id, question, options, correct_answer, created_at)
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            RETURNING id
        """,
            course_id,
            quiz.lesson_id,
            quiz.question,
            json.dumps(quiz.options),
            quiz.correct_answer
        )
        
        return {"id": quiz_id, "message": "Quiz created successfully"}

# Q&A
@router.post("/{course_id}/questions")
async def ask_question(
    course_id: int,
    question: QuestionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Ask a question about the course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        question_id = await conn.fetchval("""
            INSERT INTO student_questions (
                course_id, lesson_id, user_id, question, is_answered, created_at
            ) VALUES ($1, $2, $3, $4, FALSE, CURRENT_TIMESTAMP)
            RETURNING id
        """,
            course_id,
            question.lesson_id,
            current_user['id'],
            question.question
        )
        
        return {"id": question_id, "message": "Question submitted successfully"}
