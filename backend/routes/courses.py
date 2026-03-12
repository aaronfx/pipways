"""
Course Routes - Learning Management System
Includes: Courses, Modules, Lessons, Quizzes, Progress Tracking, Q&A
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from . import database
from .security import get_current_user, get_admin_user, get_current_user_optional
from .schemas import (
    CourseCreate, CourseUpdate, CourseResponse, CourseDetailResponse,
    ModuleCreate, ModuleUpdate, ModuleResponse,
    LessonCreate, LessonUpdate, LessonResponse, LessonMinimal,
    QuizCreate, QuizUpdate, QuizResponse, QuizSubmit, QuizResult,
    StudentQuestionCreate, StudentQuestionResponse,
    ProgressUpdate, ProgressResponse
)

router = APIRouter()

def calculate_progress(completed: int, total: int) -> int:
    """Calculate percentage with safety"""
    if total == 0:
        return 0
    return min(100, int((completed / total) * 100))

# ============================================================================
# PUBLIC COURSE VIEWING
# ============================================================================

@router.get("", response_model=List[CourseResponse])
async def get_courses(
    search: Optional[str] = None,
    level: Optional[str] = None,
    category: Optional[str] = None,
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
        
        if category:
            query += f" AND category = ${len(params)+1}"
            params.append(category)
        
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
            course_dict['total_modules'] = len(modules)
            
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
        
        return result

@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course_detail(
    course_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get full course with modules, lessons, and user progress"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course = await conn.fetchrow("""
            SELECT c.*, u.full_name as author_name 
            FROM courses c 
            LEFT JOIN users u ON c.created_by = u.id 
            WHERE c.id = $1 AND c.status = 'published'
        """, course_id)
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        course_dict = dict(course)
        course_dict['author'] = {"id": course['created_by'], "full_name": course['author_name']} if course['created_by'] else None
        
        # Get modules with lessons
        modules = await conn.fetch("""
            SELECT * FROM course_modules 
            WHERE course_id = $1 AND is_published = TRUE
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
                    END as is_completed,
                    (SELECT COUNT(*) FROM student_questions WHERE lesson_id = l.id AND is_answered = FALSE) as pending_questions
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
                SELECT * FROM quizzes WHERE module_id = $1 AND is_published = TRUE
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
        
        # Check enrollment
        if current_user:
            enrollment = await conn.fetchrow("""
                SELECT * FROM enrollments WHERE user_id = $1 AND course_id = $2 AND is_active = TRUE
            """, current_user['id'], course_id)
            course_dict['is_enrolled'] = enrollment is not None
        else:
            course_dict['is_enrolled'] = False
        
        return course_dict

@router.get("/{course_id}/lessons/{lesson_id}", response_model=LessonResponse)
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
        
        # Check if premium content
        if lesson['is_premium'] and current_user.get('subscription_tier') != 'vip':
            raise HTTPException(status_code=403, detail="VIP access required for this lesson")
        
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
            WHERE q.lesson_id = $1 AND (q.is_public = TRUE OR q.user_id = $2)
            ORDER BY q.created_at DESC
        """, lesson_id, current_user['id'])
        
        lesson_dict['questions'] = [dict(q) for q in questions]
        
        # Get adjacent lessons for navigation
        prev_lesson = await conn.fetchrow("""
            SELECT l.id FROM lessons l
            JOIN course_modules m ON l.module_id = m.id
            WHERE m.course_id = $1 AND l.sort_order < $2 AND l.module_id = $3
            ORDER BY l.sort_order DESC LIMIT 1
        """, course_id, lesson['sort_order'], lesson['module_id'])
        
        next_lesson = await conn.fetchrow("""
            SELECT l.id FROM lessons l
            JOIN course_modules m ON l.module_id = m.id
            WHERE m.course_id = $1 AND l.sort_order > $2 AND l.module_id = $3
            ORDER BY l.sort_order ASC LIMIT 1
        """, course_id, lesson['sort_order'], lesson['module_id'])
        
        if not next_lesson:
            # Try next module
            next_module_lesson = await conn.fetchrow("""
                SELECT l.id FROM lessons l
                JOIN course_modules m ON l.module_id = m.id
                WHERE m.course_id = $1 AND m.sort_order > (
                    SELECT sort_order FROM course_modules WHERE id = $2
                )
                ORDER BY m.sort_order, l.sort_order LIMIT 1
            """, course_id, lesson['module_id'])
            if next_module_lesson:
                next_lesson = next_module_lesson
        
        lesson_dict['prev_lesson'] = prev_lesson['id'] if prev_lesson else None
        lesson_dict['next_lesson'] = next_lesson['id'] if next_lesson else None
        
        # Check completion status
        progress = await conn.fetchrow("""
            SELECT completed FROM student_progress WHERE user_id = $1 AND lesson_id = $2
        """, current_user['id'], lesson_id)
        lesson_dict['is_completed'] = progress['completed'] if progress else False
        
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
            SELECT l.id, m.id as module_id, l.is_premium 
            FROM lessons l
            JOIN course_modules m ON l.module_id = m.id
            WHERE l.id = $1 AND m.course_id = $2
        """, lesson_id, course_id)
        
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Check quiz requirement
        quiz = await conn.fetchrow("""
            SELECT q.* FROM quizzes q
            JOIN course_modules m ON q.module_id = m.id
            JOIN lessons l ON l.module_id = m.id
            WHERE l.id = $1 AND q.pass_mcq_required = TRUE
        """, lesson_id)
        
        if quiz:
            # Check if passed quiz
            passed = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM quiz_attempts 
                    WHERE quiz_id = $1 AND user_id = $2 AND passed = TRUE
                )
            """, quiz['id'], current_user['id'])
            
            if not passed:
                raise HTTPException(status_code=400, detail="Must pass module quiz before completing this lesson")
        
        await conn.execute("""
            INSERT INTO student_progress 
            (user_id, course_id, module_id, lesson_id, completed, completed_at, progress_percent)
            VALUES ($1, $2, $3, $4, TRUE, CURRENT_TIMESTAMP, 100)
            ON CONFLICT (user_id, lesson_id) 
            DO UPDATE SET completed = TRUE, completed_at = CURRENT_TIMESTAMP, progress_percent = 100
        """, current_user['id'], course_id, lesson['module_id'], lesson_id)
        
        return {"message": "Lesson marked as complete"}

@router.post("/{course_id}/enroll")
async def enroll_in_course(
    course_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Enroll user in course"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        try:
            await conn.execute("""
                INSERT INTO enrollments (user_id, course_id, payment_status)
                VALUES ($1, $2, $3)
            """, current_user['id'], course_id, 'free' if course['price'] == 0 else 'pending')
            
            return {"message": "Enrolled successfully"}
        except asyncpg.exceptions.UniqueViolationError:
            return {"message": "Already enrolled"}

# ============================================================================
# QUIZZES
# ============================================================================

@router.get("/{course_id}/modules/{module_id}/quiz", response_model=QuizResponse)
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
            SELECT q.* FROM quizzes q
            JOIN course_modules m ON q.module_id = m.id
            WHERE q.module_id = $1 AND m.course_id = $2 AND q.is_published = TRUE
        """, module_id, course_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="No quiz found for this module")
        
        quiz_dict = dict(quiz)
        
        questions = await conn.fetch("""
            SELECT id, question_text, question_type, options, points, sort_order, image_url
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

@router.post("/{course_id}/modules/{module_id}/quiz/submit", response_model=QuizResult)
async def submit_quiz(
    course_id: int,
    module_id: int,
    data: QuizSubmit,
    current_user: dict = Depends(get_current_user)
):
    """Submit quiz answers and grade"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        quiz = await conn.fetchrow("""
            SELECT q.* FROM quizzes q
            JOIN course_modules m ON q.module_id = m.id
            WHERE q.module_id = $1 AND m.course_id = $2
        """, module_id, course_id)
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Check attempt limits
        attempt_count = await conn.fetchval("""
            SELECT COUNT(*) FROM quiz_attempts WHERE quiz_id = $1 AND user_id = $2
        """, quiz['id'], current_user['id'])
        
        if attempt_count >= quiz['max_attempts']:
            raise HTTPException(status_code=400, detail=f"Maximum attempts ({quiz['max_attempts']}) reached")
        
        # Get questions with correct answers
        questions = await conn.fetch("""
            SELECT id, correct_answer, correct_answers, points FROM quiz_questions WHERE quiz_id = $1
        """, quiz['id'])
        
        # Calculate score
        score = 0
        max_score = 0
        for q in questions:
            max_score += q['points']
            user_answer = data.answers.get(str(q['id']))
            
            if user_answer:
                # Handle multiple correct answers
                correct = [q['correct_answer']]
                if q['correct_answers']:
                    correct = json.loads(q['correct_answers']) if isinstance(q['correct_answers'], str) else q['correct_answers']
                
                if user_answer.lower() in [c.lower() for c in correct]:
                    score += q['points']
        
        percentage = (score / max_score * 100) if max_score > 0 else 0
        passed = percentage >= quiz['passing_score']
        
        attempt_id = await conn.fetchval("""
            INSERT INTO quiz_attempts 
            (quiz_id, user_id, answers, score, max_score, percentage, passed, attempt_number, time_taken_seconds, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP)
            RETURNING id
        """, 
            quiz['id'], 
            current_user['id'], 
            json.dumps(data.answers),
            score, 
            max_score, 
            round(percentage, 2),
            passed,
            attempt_count + 1,
            data.time_taken
        )
        
        return {
            "attempt_id": attempt_id,
            "score": score,
            "max_score": max_score,
            "percentage": round(percentage, 2),
            "passed": passed,
            "attempt_number": attempt_count + 1
        }

# ============================================================================
# STUDENT Q&A
# ============================================================================

@router.post("/{course_id}/lessons/{lesson_id}/questions")
async def ask_question(
    course_id: int,
    lesson_id: int,
    question: StudentQuestionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Student asks a question about a lesson"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        question_id = await conn.fetchval("""
            INSERT INTO student_questions (lesson_id, user_id, question, question_type)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, lesson_id, current_user['id'], question.question, question.question_type)
        
        return {"id": question_id, "message": "Question submitted"}

@router.get("/questions/pending")
async def get_pending_questions(current_user: dict = Depends(get_admin_user)):
    """Get all unanswered questions (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        questions = await conn.fetch("""
            SELECT q.*, u.full_name as student_name, l.title as lesson_title, c.title as course_title
            FROM student_questions q
            JOIN users u ON q.user_id = u.id
            JOIN lessons l ON q.lesson_id = l.id
            JOIN course_modules m ON l.module_id = m.id
            JOIN courses c ON m.course_id = c.id
            WHERE q.is_answered = FALSE
            ORDER BY q.created_at DESC
        """)
        
        return [dict(q) for q in questions]

@router.post("/questions/{question_id}/answer")
async def answer_question(
    question_id: int,
    answer: str,
    current_user: dict = Depends(get_admin_user)
):
    """Admin answers a student question"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE student_questions 
            SET answer = $1, answered_by = $2, is_answered = TRUE, answered_at = CURRENT_TIMESTAMP
            WHERE id = $3
        """, answer, current_user['id'], question_id)
        
        return {"message": "Answer submitted"}

# ============================================================================
# ADMIN COURSE MANAGEMENT
# ============================================================================

@router.post("", response_model=CourseResponse)
async def create_course(course: CourseCreate, current_user: dict = Depends(get_admin_user)):
    """Create new course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        course_id = await conn.fetchval("""
            INSERT INTO courses (title, description, short_description, thumbnail, level, duration_hours, 
                is_premium, status, price, currency, category, tags, prerequisites, learning_outcomes, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING id
        """,
            course.title, course.description, course.short_description, course.thumbnail,
            course.level, course.duration_hours, course.is_premium, course.status,
            course.price, course.currency, course.category, course.tags,
            course.prerequisites, course.learning_outcomes, current_user['id']
        )
        
        return await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)

@router.put("/{course_id}")
async def update_course(
    course_id: int,
    course: CourseUpdate,
    current_user: dict = Depends(get_admin_user)
):
    """Update course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM courses WHERE id = $1", course_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Build dynamic update
        updates = []
        values = []
        for field, value in course.dict(exclude_unset=True).items():
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
async def delete_course(course_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete course (Admin only)"""
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
    """Add module to course (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        max_order = await conn.fetchval("""
            SELECT COALESCE(MAX(sort_order), 0) FROM course_modules WHERE course_id = $1
        """, course_id)
        
        module_id = await conn.fetchval("""
            INSERT INTO course_modules (course_id, title, description, sort_order, is_premium, is_published)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, course_id, module.title, module.description, max_order + 1, module.is_premium, module.is_published)
        
        return {"id": module_id, "message": "Module created successfully"}

@router.post("/{course_id}/modules/{module_id}/lessons")
async def create_lesson(
    course_id: int,
    module_id: int,
    lesson: LessonCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Add lesson to module (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Verify module belongs to course
        module = await conn.fetchrow("""
            SELECT id FROM course_modules WHERE id = $1 AND course_id = $2
        """, module_id, course_id)
        
        if not module:
            raise HTTPException(status_code=404, detail="Module not found in this course")
        
        max_order = await conn.fetchval("""
            SELECT COALESCE(MAX(sort_order), 0) FROM lessons WHERE module_id = $1
        """, module_id)
        
        lesson_id = await conn.fetchval("""
            INSERT INTO lessons (
                module_id, title, content, video_url, video_type, pdf_url, 
                images, duration_minutes, is_premium, is_preview, pass_mcq_required, sort_order
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
        """,
            module_id, lesson.title, lesson.content, lesson.video_url,
            lesson.video_type, lesson.pdf_url, lesson.images,
            lesson.duration_minutes, lesson.is_premium, lesson.is_preview,
            lesson.pass_mcq_required, max_order + 1
        )
        
        return {"id": lesson_id, "message": "Lesson created successfully"}

@router.post("/{course_id}/modules/{module_id}/quizzes")
async def create_quiz(
    course_id: int,
    module_id: int,
    quiz: QuizCreate,
    current_user: dict = Depends(get_admin_user)
):
    """Create quiz for module (Admin only)"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        quiz_id = await conn.fetchval("""
            INSERT INTO quizzes (module_id, title, description, instructions, passing_score, 
                time_limit_minutes, max_attempts, shuffle_questions, show_correct_answers, is_published)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        """, module_id, quiz.title, quiz.description, quiz.instructions,
            quiz.passing_score, quiz.time_limit_minutes, quiz.max_attempts,
            quiz.shuffle_questions, quiz.show_correct_answers, quiz.is_published)
        
        # Add questions
        for idx, q in enumerate(quiz.questions):
            await conn.execute("""
                INSERT INTO quiz_questions 
                (quiz_id, question_text, question_type, options, correct_answer, correct_answers, 
                 explanation, hint, points, sort_order, image_url)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                quiz_id, q.question_text, q.question_type, 
                json.dumps(q.options) if q.options else None,
                q.correct_answer,
                json.dumps(q.correct_answers) if q.correct_answers else None,
                q.explanation, q.hint, q.points, idx, q.image_url
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
                (SELECT COUNT(DISTINCT user_id) FROM enrollments) as total_students,
                (SELECT COUNT(*) FROM student_questions WHERE is_answered = FALSE) as pending_questions
        """)
        
        return dict(stats)
