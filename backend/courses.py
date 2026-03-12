"""Enhanced LMS Routes with Lessons, Quizzes, Progress Tracking"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from . import database
from .security import get_current_user, get_current_user_optional, get_admin_user
from .schemas import CourseCreate, ModuleCreate, LessonCreate, QuizCreate, QuestionCreate

router = APIRouter()

def calculate_progress(completed: int, total: int) -> int:
    """Calculate percentage with safety"""
    if total == 0:
        return 0
    return min(100, int((completed / total) * 100))

# ============ PUBLIC COURSE VIEWING ============

@router.get("")
async def get_courses(
    search: Optional[str] = None,
    level: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get all published courses with user progress"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = "SELECT * FROM courses WHERE status = 'published'"
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
            
            # Get modules with lesson counts
            modules = await conn.fetch("""
                SELECT m.*, 
                    (SELECT COUNT(*) FROM lessons WHERE module_id = m.id) as lesson_count,
                    (SELECT COALESCE(SUM(duration_minutes), 0) FROM lessons WHERE module_id = m.id) as total_duration
                FROM course_modules m 
                WHERE m.course_id = $1 
                ORDER BY m.sort_order
            """, course['id'])
            
            course_dict['modules'] = [dict(m) for m in modules]
            total_lessons = sum(m['lesson_count'] for m in course_dict['modules'])
            course_dict['total_lessons'] = total_lessons
            
            # Calculate progress for logged-in users
            if current_user:
                if total_lessons > 0:
                    completed = await conn.fetchval("""
                        SELECT COUNT(*) FROM student_progress 
                        WHERE user_id = $1 AND course_id = $2 AND completed = TRUE
                    """, current_user['id'], course['id'])
                    course_dict['progress_percent'] = calculate_progress(completed, total_lessons)
                    course_dict['completed_lessons'] = completed
                    course_dict['is_enrolled'] = True
                else:
                    course_dict['progress_percent'] = 0
                    course_dict['completed_lessons'] = 0
            else:
                course_dict['progress_percent'] = 0
                course_dict['is_enrolled'] = False
            
            result.append(course_dict)
        
        return {"courses": result}

@router.get("/{course_id}")
async def get_course_detail(
    course_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get full course with modules, lessons, and user progress"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course = await conn.fetchrow(
            "SELECT * FROM courses WHERE id = $1 AND status = 'published'", 
            course_id
        )
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        course_dict = dict(course)
        
        # Get modules with lessons
        modules = await conn.fetch("""
            SELECT * FROM course_modules 
            WHERE course_id = $1 
            ORDER BY sort_order
        """, course_id)
        
        course_dict['modules'] = []
        total_lessons = 0
        completed_lessons = 0
        
        for module in modules:
            module_dict = dict(module)
            
            lessons = await conn.fetch("""
                SELECT l.*,
                    CASE WHEN $1::int IS NULL THEN FALSE
                    ELSE EXISTS(
                        SELECT 1 FROM student_progress 
                        WHERE user_id = $1 AND lesson_id = l.id AND completed = TRUE
                    )
                    END as is_completed
                FROM lessons l
                WHERE l.module_id = $2
                ORDER BY l.sort_order
            """, current_user['id'] if current_user else None, module['id'])
            
            module_dict['lessons'] = [dict(l) for l in lessons]
            total_lessons += len(lessons)
            
            if current_user:
                completed_lessons += sum(1 for l in lessons if l['is_completed'])
            
            # Get quiz for this module
            quiz = await conn.fetchrow("""
                SELECT * FROM quizzes WHERE module_id = $1
            """, module['id'])
            
            if quiz:
                module_dict['quiz'] = dict(quiz)
                # Get quiz attempts if user is logged in
                if current_user:
                    attempts = await conn.fetch("""
                        SELECT * FROM quiz_attempts 
                        WHERE quiz_id = $1 AND user_id = $2
                        ORDER BY completed_at DESC
                    """, quiz['id'], current_user['id'])
                    module_dict['quiz']['attempts'] = [dict(a) for a in attempts]
            
            course_dict['modules'].append(module_dict)
        
        course_dict['total_lessons'] = total_lessons
        course_dict['completed_lessons'] = completed_lessons
        course_dict['progress_percent'] = calculate_progress(completed_lessons, total_lessons)
        
        return course_dict

@router.get("/{course_id}/lessons/{lesson_id}")
async def get_lesson_detail(
    course_id: int,
    lesson_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get lesson content with Q&A"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Verify lesson exists and belongs to course
        lesson = await conn.fetchrow("""
            SELECT l.*, m.course_id, m.id as module_id
            FROM lessons l
            JOIN course_modules m ON l.module_id = m.id
            WHERE l.id = $1 AND m.course_id = $2
        """, lesson_id, course_id)
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        lesson_dict = dict(lesson)
        
        # Update last accessed
        await conn.execute("""
            INSERT INTO student_progress (user_id, course_id, module_id, lesson_id, last_accessed)
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, lesson_id) 
            DO UPDATE SET last_accessed = CURRENT_TIMESTAMP
        """, current_user['id'], course_id, lesson['module_id'], lesson_id)
        
        # Get Q&A for this lesson
        questions = await conn.fetch("""
            SELECT q.*, u.full_name as student_name, a.full_name as answered_by_name
            FROM student_questions q
            JOIN users u ON q.user_id = u.id
            LEFT JOIN users a ON q.answered_by = a.id
            WHERE q.lesson_id = $1
            ORDER BY q.created_at DESC
        """, lesson_id)
        
        lesson_dict['questions'] = [dict(q) for q in questions]
        
        # Get adjacent lessons for navigation
        prev_lesson = await conn.fetchrow("""
            SELECT l.id FROM lessons l
            JOIN course_modules m ON l.module_id = m.id
            WHERE m.course_id = $1 AND l.id < $2
            ORDER BY l.id DESC LIMIT 1
        """, course_id, lesson_id)
        
        next_lesson = await conn.fetchrow("""
            SELECT l.id FROM lessons l
            JOIN course_modules m ON l.module_id = m.id
            WHERE m.course_id = $1 AND l.id > $2
            ORDER BY l.id ASC LIMIT 1
        """, course_id, lesson_id)
        
        lesson_dict['prev_lesson'] = prev_lesson['id'] if prev_lesson else None
        lesson_dict['next_lesson'] = next_lesson['id'] if next_lesson else None
        
        return lesson_dict

@router.post("/{course_id}/lessons/{lesson_id}/complete")
async def mark_lesson_complete(
    course_id: int,
    lesson_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Mark lesson as completed"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Get module_id for this lesson
        lesson = await conn.fetchrow("""
            SELECT l.id, m.id as module_id 
            FROM lessons l
            JOIN course_modules m ON l.module_id = m.id
            WHERE l.id = $1 AND m.course_id = $2
        """, lesson_id, course_id)
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        await conn.execute("""
            INSERT INTO student_progress 
            (user_id, course_id, module_id, lesson_id, completed, completed_at, progress_percent)
            VALUES ($1, $2, $3, $4, TRUE, CURRENT_TIMESTAMP, 100)
            ON CONFLICT (user_id, lesson_id) 
            DO UPDATE SET completed = TRUE, completed_at = CURRENT_TIMESTAMP, progress_percent = 100
        """, current_user['id'], course_id, lesson['module_id'], lesson_id)
        
        return {"message": "Lesson marked as complete"}

@router.post("/{course_id}/lessons/{lesson_id}/questions")
async def ask_question(
    course_id: int,
    lesson_id: int,
    question: str,
    current_user: dict = Depends(get_current_user)
):
    """Student asks a question about a lesson"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        question_id = await conn.fetchval("""
            INSERT INTO student_questions (lesson_id, user_id, question)
            VALUES ($1, $2, $3)
            RETURNING id
        """, lesson_id, current_user['id'], question)
        
        return {"id": question_id, "message": "Question submitted"}

# ============ QUIZZES ============

@router.get("/{course_id}/modules/{module_id}/quiz")
async def get_quiz(
    course_id: int,
    module_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get quiz with questions for a module"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        quiz = await conn.fetchrow("""
            SELECT * FROM quizzes WHERE module_id = $1
        """, module_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="No quiz found for this module")
        
        quiz_dict = dict(quiz)
        
        questions = await conn.fetch("""
            SELECT id, question_text, question_type, options, points, sort_order
            FROM quiz_questions
            WHERE quiz_id = $1
            ORDER BY sort_order
        """, quiz['id'])
        
        quiz_dict['questions'] = [dict(q) for q in questions]
        
        # Get previous attempts
        attempts = await conn.fetch("""
            SELECT * FROM quiz_attempts
            WHERE quiz_id = $1 AND user_id = $2
            ORDER BY completed_at DESC
        """, quiz['id'], current_user['id'])
        
        quiz_dict['attempts'] = [dict(a) for a in attempts]
        
        return quiz_dict

@router.post("/{course_id}/modules/{module_id}/quiz/submit")
async def submit_quiz(
    course_id: int,
    module_id: int,
    answers: Dict[str, str],
    time_taken: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Submit quiz answers and grade"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        quiz = await conn.fetchrow("SELECT * FROM quizzes WHERE module_id = $1", module_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get questions with correct answers
        questions = await conn.fetch("""
            SELECT id, correct_answer, points FROM quiz_questions WHERE quiz_id = $1
        """, quiz['id'])
        
        # Calculate score
        score = 0
        max_score = 0
        for q in questions:
            max_score += q['points']
            user_answer = answers.get(str(q['id']))
            if user_answer and user_answer.lower() == q['correct_answer'].lower():
                score += q['points']
        
        percentage = (score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= quiz['passing_score']
        
        # Check attempt number
        prev_attempts = await conn.fetchval("""
            SELECT COUNT(*) FROM quiz_attempts WHERE quiz_id = $1 AND user_id = $2
        """, quiz['id'], current_user['id'])
        
        attempt_id = await conn.fetchval("""
            INSERT INTO quiz_attempts 
            (quiz_id, user_id, answers, score, max_score, percentage, passed, attempt_number, time_taken_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """, 
            quiz['id'], 
            current_user['id'], 
            json.dumps(answers),
            score, 
            max_score, 
            percentage,
            passed,
            prev_attempts + 1,
            time_taken
        )
        
        return {
            "attempt_id": attempt_id,
            "score": score,
            "max_score": max_score,
            "percentage": round(percentage, 2),
            "passed": passed,
            "attempt_number": prev_attempts + 1
        }

# ============ ADMIN COURSE MANAGEMENT ============

@router.post("")
async def create_course(course: CourseCreate, current_user: dict = Depends(get_admin_user)):
    """Create new course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, level, duration_hours, is_premium, status, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, 
            course.title, 
            course.description, 
            course.level,
            course.duration_hours,
            course.is_premium,
            course.status,
            current_user['id']
        )
        
        return {"id": course_id, "message": "Course created successfully"}

@router.put("/{course_id}")
async def update_course(
    course_id: int,
    course: CourseCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Update course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE courses 
            SET title = $1, description = $2, level = $3, duration_hours = $4,
                is_premium = $5, status = $6, thumbnail = $7, updated_at = CURRENT_TIMESTAMP
            WHERE id = $8
        """, 
            course.title, course.description, course.level,
            course.duration_hours, course.is_premium, course.status,
            course.thumbnail, course_id
        )
        
        return {"message": "Course updated successfully"}

@router.delete("/{course_id}")
async def delete_course(course_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("DELETE FROM courses WHERE id = $1", course_id)
        return {"message": "Course deleted successfully"}

@router.post("/{course_id}/modules")
async def create_module(
    course_id: int,
    module: ModuleCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Add module to course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Get next sort order
        max_order = await conn.fetchval("""
            SELECT COALESCE(MAX(sort_order), 0) FROM course_modules WHERE course_id = $1
        """, course_id)
        
        module_id = await conn.fetchval("""
            INSERT INTO course_modules (course_id, title, description, sort_order, is_premium)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, course_id, module.title, module.description, max_order + 1, module.is_premium)
        
        return {"id": module_id, "message": "Module created successfully"}

@router.post("/{course_id}/modules/{module_id}/lessons")
async def create_lesson(
    course_id: int,
    module_id: int,
    lesson: LessonCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Add lesson to module"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        max_order = await conn.fetchval("""
            SELECT COALESCE(MAX(sort_order), 0) FROM lessons WHERE module_id = $1
        """, module_id)
        
        lesson_id = await conn.fetchval("""
            INSERT INTO lessons (
                module_id, title, content, video_url, video_type, pdf_url, 
                images, duration_minutes, is_premium, sort_order
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        """, 
            module_id, lesson.title, lesson.content, lesson.video_url,
            lesson.video_type, lesson.pdf_url, lesson.images,
            lesson.duration_minutes, lesson.is_premium, max_order + 1
        )
        
        return {"id": lesson_id, "message": "Lesson created successfully"}

@router.post("/{course_id}/modules/{module_id}/quizzes")
async def create_quiz(
    course_id: int,
    module_id: int,
    quiz: QuizCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create quiz for module"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        quiz_id = await conn.fetchval("""
            INSERT INTO quizzes (module_id, title, description, passing_score, time_limit_minutes, max_attempts)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, module_id, quiz.title, quiz.description, quiz.passing_score, quiz.time_limit_minutes, quiz.max_attempts)
        
        # Add questions
        for idx, q in enumerate(quiz.questions):
            await conn.execute("""
                INSERT INTO quiz_questions 
                (quiz_id, question_text, question_type, options, correct_answer, explanation, points, sort_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                quiz_id, q.question_text, q.question_type, 
                json.dumps(q.options), q.correct_answer,
                q.explanation, q.points, idx
            )
        
        return {"id": quiz_id, "message": "Quiz created successfully"}

@router.get("/admin/dashboard")
async def get_course_stats(current_user: dict = Depends(get_admin_user)):
    """Get course statistics for admin dashboard"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM courses) as total_courses,
                (SELECT COUNT(*) FROM courses WHERE status = 'published') as published_courses,
                (SELECT COUNT(*) FROM course_modules) as total_modules,
                (SELECT COUNT(*) FROM lessons) as total_lessons,
                (SELECT COUNT(*) FROM quizzes) as total_quizzes,
                (SELECT COUNT(DISTINCT user_id) FROM student_progress WHERE completed = TRUE) as total_students,
                (SELECT COUNT(*) FROM student_questions WHERE is_answered = FALSE) as pending_questions
        """)
        
        return dict(stats)
