"""
Courses API - PRODUCTION READY with CMS Integration
Returns real course data with module/lesson counts from CMS
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from .database import database
from .security import get_current_user, get_user_id

router = APIRouter()

@router.get("/list")
async def get_courses(current_user = Depends(get_current_user)):
    """
    Get all available courses with user's progress and CMS curriculum counts.
    """
    try:
        user_id = get_user_id(current_user)
        
        # FIXED: Query counts modules and lessons from CMS tables
        query = """
            SELECT 
                c.id, c.title, c.description, c.level,
                c.thumbnail, c.preview_video, c.price,
                c.is_published, c.is_active,
                COALESCE(c.certificate_enabled, false) as certificate_enabled,
                COALESCE(c.pass_percentage, 70) as pass_percentage,
                COUNT(DISTINCT m.id) as module_count,
                COUNT(DISTINCT l.id) as lesson_count,
                COALESCE(up.progress_percent, 0) as progress,
                COALESCE(up.completed_lessons, 0) as completed_lessons
            FROM courses c
            LEFT JOIN course_modules m ON m.course_id = c.id
            LEFT JOIN lessons l ON l.course_id = c.id
            LEFT JOIN user_progress up ON c.id = up.course_id AND up.user_id = :user_id
            WHERE c.is_active = TRUE OR c.is_published = TRUE
            GROUP BY c.id, up.progress_percent, up.completed_lessons
            ORDER BY c.created_at DESC
        """
        
        rows = await database.fetch_all(query, {"user_id": user_id})
        
        courses = []
        for row in rows:
            courses.append({
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "level": row["level"] or "Beginner",
                "module_count": row.get("module_count", 0),
                "lesson_count": row.get("lesson_count", 0),
                "thumbnail_url": row.get("thumbnail") or row.get("thumbnail_url", ""),
                "preview_video": row.get("preview_video", ""),
                "price": float(row.get("price", 0)),
                "progress": row.get("progress", 0),
                "completed_lessons": row.get("completed_lessons", 0),
                "certificate_enabled": row.get("certificate_enabled", False),
                "pass_percentage": row.get("pass_percentage", 70),
                "is_published": row.get("is_published", False),
            })
        
        return courses

    except Exception as e:
        print(f"[COURSES ERROR] {e}", flush=True)
        raise HTTPException(500, "Failed to load courses")

@router.get("/{course_id}/curriculum")
async def get_course_curriculum(
    course_id: int, 
    current_user = Depends(get_current_user)
):
    """
    Get full curriculum structure: Modules → Lessons → Quiz availability
    """
    try:
        # Verify course exists and is published
        course = await database.fetch_one(
            """SELECT id, title, description, level, thumbnail, preview_video, 
               price, certificate_enabled, pass_percentage
               FROM courses 
               WHERE id = :id AND (is_active = TRUE OR is_published = TRUE)""",
            {"id": course_id}
        )
        
        if not course:
            raise HTTPException(404, "Course not found")
        
        # Get modules with lesson counts
        modules_query = """
            SELECT 
                m.id, m.title, m.description, m.order_index,
                COUNT(l.id) as lesson_count,
                (SELECT COUNT(*) FROM quizzes q WHERE q.module_id = m.id) as has_quiz
            FROM course_modules m
            LEFT JOIN lessons l ON l.module_id = m.id
            WHERE m.course_id = :course_id
            GROUP BY m.id
            ORDER BY m.order_index, m.id
        """
        modules = await database.fetch_all(modules_query, {"course_id": course_id})
        
        curriculum = []
        for module in modules:
            # Get lessons for this module
            lessons = await database.fetch_all(
                """SELECT id, title, content, video_url, attachment_url, 
                   duration_minutes, order_index, is_free_preview
                   FROM lessons 
                   WHERE module_id = :mid 
                   ORDER BY order_index, id""",
                {"mid": module["id"]}
            )
            
            # Get quiz if exists
            quiz = await database.fetch_one(
                "SELECT id, title, pass_percentage FROM quizzes WHERE module_id = :mid",
                {"mid": module["id"]}
            )
            
            lesson_list = []
            for lesson in lessons:
                # Check completion status
                completed = await database.fetch_one(
                    """SELECT 1 FROM user_lesson_progress 
                       WHERE user_id = :uid AND lesson_id = :lid""",
                    {"uid": get_user_id(current_user), "lid": lesson["id"]}
                )
                
                lesson_list.append({
                    "id": lesson["id"],
                    "title": lesson["title"],
                    "video_url": lesson["video_url"],
                    "duration_minutes": lesson["duration_minutes"] or 0,
                    "is_free_preview": lesson["is_free_preview"] or False,
                    "completed": completed is not None
                })
            
            mod_data = {
                "id": module["id"],
                "title": module["title"],
                "description": module["description"],
                "order_index": module["order_index"],
                "lessons": lesson_list,
                "quiz": {
                    "id": quiz["id"],
                    "title": quiz["title"],
                    "pass_percentage": quiz["pass_percentage"]
                } if quiz else None
            }
            curriculum.append(mod_data)
        
        return {
            "course": dict(course),
            "modules": curriculum
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CURRICULUM ERROR] {e}", flush=True)
        raise HTTPException(500, "Failed to load curriculum")

@router.post("/{course_id}/lessons/{lesson_id}/complete")
async def complete_lesson(
    course_id: int,
    lesson_id: int,
    current_user = Depends(get_current_user)
):
    """
    Mark lesson as complete and recalculate course progress.
    """
    try:
        user_id = get_user_id(current_user)
        
        # Verify lesson exists and belongs to course
        lesson = await database.fetch_one(
            """SELECT l.*, m.course_id 
               FROM lessons l 
               JOIN course_modules m ON l.module_id = m.id
               WHERE l.id = :lid AND m.course_id = :cid""",
            {"lid": lesson_id, "cid": course_id}
        )
        
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        
        # Insert completion record (idempotent)
        await database.execute(
            """INSERT INTO user_lesson_progress (user_id, lesson_id, completed_at, time_spent_seconds)
               VALUES (:uid, :lid, NOW(), 0)
               ON CONFLICT (user_id, lesson_id) DO UPDATE SET completed_at = NOW()""",
            {"uid": user_id, "lid": lesson_id}
        )
        
        # Calculate new progress
        total_lessons = await database.fetch_val(
            """SELECT COUNT(*) FROM lessons l
               JOIN course_modules m ON l.module_id = m.id
               WHERE m.course_id = :cid""",
            {"cid": course_id}
        ) or 1
        
        completed_count = await database.fetch_val(
            """SELECT COUNT(*) FROM user_lesson_progress ulp
               JOIN lessons l ON ulp.lesson_id = l.id
               JOIN course_modules m ON l.module_id = m.id
               WHERE ulp.user_id = :uid AND m.course_id = :cid""",
            {"uid": user_id, "cid": course_id}
        ) or 0
        
        progress_percent = int((completed_count / total_lessons) * 100)
        is_completed = progress_percent == 100
        
        # Update or create user_progress
        existing = await database.fetch_one(
            "SELECT id FROM user_progress WHERE user_id = :uid AND course_id = :cid",
            {"uid": user_id, "cid": course_id}
        )
        
        if existing:
            await database.execute(
                """UPDATE user_progress 
                   SET progress_percent = :prog,
                       completed_lessons = :completed,
                       completed_at = CASE WHEN :completed THEN NOW() ELSE completed_at END,
                       last_accessed = NOW()
                   WHERE user_id = :uid AND course_id = :cid""",
                {
                    "prog": progress_percent,
                    "completed": completed_count,
                    "uid": user_id,
                    "cid": course_id
                }
            )
        else:
            await database.execute(
                """INSERT INTO user_progress 
                   (user_id, course_id, progress_percent, completed_lessons, last_accessed)
                   VALUES (:uid, :cid, :prog, :completed, NOW())""",
                {
                    "uid": user_id,
                    "cid": course_id,
                    "prog": progress_percent,
                    "completed": completed_count
                }
            )
        
        # Check for certificate eligibility
        certificate = None
        if is_completed:
            cert_check = await database.fetch_one(
                "SELECT id FROM certificates WHERE user_id = :uid AND course_id = :cid",
                {"uid": user_id, "cid": course_id}
            )
            if not cert_check:
                cert_id = f"CERT-{user_id}-{course_id}-{datetime.utcnow().strftime('%Y%m%d')}"
                await database.execute(
                    """INSERT INTO certificates (user_id, course_id, certificate_number, issued_at)
                       VALUES (:uid, :cid, :cert_num, NOW())""",
                    {"uid": user_id, "cid": course_id, "cert_num": cert_id}
                )
                certificate = cert_id
        
        return {
            "lesson_completed": True,
            "progress_percent": progress_percent,
            "course_completed": is_completed,
            "certificate_issued": certificate is not None,
            "certificate_id": certificate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[COMPLETE LESSON ERROR] {e}", flush=True)
        raise HTTPException(500, "Failed to update progress")

@router.get("/{course_id}/quizzes/{quiz_id}")
async def get_quiz(
    course_id: int, 
    quiz_id: int,
    current_user = Depends(get_current_user)
):
    """
    Get quiz questions for student (no correct answers exposed).
    """
    try:
        # Verify quiz belongs to course
        quiz = await database.fetch_one(
            """SELECT q.* FROM quizzes q
               JOIN course_modules m ON q.module_id = m.id
               WHERE q.id = :qid AND m.course_id = :cid""",
            {"qid": quiz_id, "cid": course_id}
        )
        
        if not quiz:
            raise HTTPException(404, "Quiz not found")
        
        # Get questions without correct answers
        questions = await database.fetch_all(
            """SELECT id, question, option_a, option_b, option_c, option_d, order_index
               FROM quiz_questions 
               WHERE quiz_id = :qid 
               ORDER BY order_index""",
            {"qid": quiz_id}
        )
        
        return {
            "id": quiz["id"],
            "title": quiz["title"],
            "pass_percentage": quiz["pass_percentage"],
            "max_attempts": quiz["max_attempts"],
            "questions": [dict(q) for q in questions]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[GET QUIZ ERROR] {e}", flush=True)
        raise HTTPException(500, "Failed to load quiz")

@router.post("/{course_id}/quizzes/{quiz_id}/submit")
async def submit_quiz(
    course_id: int,
    quiz_id: int,
    answers: dict,  # {question_id: "a" | "b" | "c" | "d"}
    current_user = Depends(get_current_user)
):
    """
    Submit quiz answers and return results.
    """
    try:
        # Get correct answers
        questions = await database.fetch_all(
            "SELECT id, correct_option FROM quiz_questions WHERE quiz_id = :qid",
            {"qid": quiz_id}
        )
        
        if not questions:
            raise HTTPException(404, "Quiz questions not found")
        
        quiz = await database.fetch_one(
            "SELECT pass_percentage, max_attempts FROM quizzes WHERE id = :qid",
            {"qid": quiz_id}
        )
        
        total = len(questions)
        correct = 0
        results = []
        
        for q in questions:
            user_answer = answers.get(str(q["id"]), "").lower()
            is_correct = user_answer == q["correct_option"].lower()
            if is_correct:
                correct += 1
            
            results.append({
                "question_id": q["id"],
                "user_answer": user_answer,
                "correct_answer": q["correct_option"],
                "is_correct": is_correct
            })
        
        score = int((correct / total) * 100)
        passed = score >= (quiz["pass_percentage"] or 70)
        
        return {
            "score": score,
            "passed": passed,
            "correct_count": correct,
            "total_questions": total,
            "passing_score": quiz["pass_percentage"] or 70,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SUBMIT QUIZ ERROR] {e}", flush=True)
        raise HTTPException(500, "Failed to submit quiz")
