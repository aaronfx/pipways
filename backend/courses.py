"""
Courses LMS API - PRODUCTION READY
Endpoints:
  GET  /courses/list
  GET  /courses/{id}
  GET  /courses/{id}/curriculum
  POST /courses/{id}/lessons/{lesson_id}/complete
  GET  /courses/{id}/quizzes/{quiz_id}
  POST /courses/{id}/quizzes/{quiz_id}/submit
"""
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from .database import database
from .security import get_current_user, get_user_id

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row(r) -> dict:
    return dict(r) if r else {}


async def _safe(query: str, params: dict = None):
    """Execute a fetch_all silently returning [] on error."""
    try:
        return await database.fetch_all(query, params or {})
    except Exception:
        return []


async def _safe_one(query: str, params: dict = None):
    """Execute a fetch_one silently returning None on error."""
    try:
        return await database.fetch_one(query, params or {})
    except Exception:
        return None


# ── Course listing ────────────────────────────────────────────────────────────

@router.get("/list")
async def list_courses(current_user=Depends(get_current_user)):
    """
    Return all published courses with the current user's progress.
    Falls back gracefully if LMS columns or tables don't exist yet.
    """
    user_id = get_user_id(current_user)

    try:
        rows = await database.fetch_all(
            """
            SELECT c.id, c.title, c.description, c.level,
                   COALESCE(c.lesson_count, 0)       AS lesson_count,
                   COALESCE(c.thumbnail_url, c.thumbnail, '') AS thumbnail_url,
                   COALESCE(c.instructor, '')         AS instructor,
                   COALESCE(up.progress_percent, 0)  AS progress,
                   COALESCE(up.completed_lessons, 0) AS completed_lessons
            FROM courses c
            LEFT JOIN user_progress up
                   ON c.id = up.course_id AND up.user_id = :uid
            WHERE COALESCE(c.is_active, TRUE) = TRUE
               OR COALESCE(c.is_published, FALSE) = TRUE
            ORDER BY c.created_at DESC
            """,
            {"uid": user_id},
        )
    except Exception:
        # Fallback: user_progress table or new columns may not exist
        rows = await _safe(
            """
            SELECT id, title, description, level,
                   COALESCE(lesson_count, 0) AS lesson_count,
                   COALESCE(thumbnail_url, '') AS thumbnail_url,
                   COALESCE(instructor, '') AS instructor
            FROM courses
            WHERE COALESCE(is_active, TRUE) = TRUE
               OR COALESCE(is_published, FALSE) = TRUE
            ORDER BY created_at DESC
            """
        )

    return [
        {
            "id":                r["id"],
            "title":             r["title"],
            "description":       r.get("description", ""),
            "level":             r.get("level", "Beginner"),
            "lesson_count":      r.get("lesson_count", 0),
            "thumbnail_url":     r.get("thumbnail_url", ""),
            "instructor":        r.get("instructor", ""),
            "progress":          r.get("progress", 0),
            "completed_lessons": r.get("completed_lessons", 0),
        }
        for r in rows
    ]


# ── Course detail ─────────────────────────────────────────────────────────────

@router.get("/{course_id}")
async def get_course(course_id: int, current_user=Depends(get_current_user)):
    row = await _safe_one(
        "SELECT * FROM courses WHERE id = :id AND (COALESCE(is_active,TRUE)=TRUE OR COALESCE(is_published,FALSE)=TRUE)",
        {"id": course_id},
    )
    if not row:
        raise HTTPException(404, "Course not found")
    return _row(row)


# ── Curriculum ────────────────────────────────────────────────────────────────

@router.get("/{course_id}/curriculum")
async def get_curriculum(course_id: int, current_user=Depends(get_current_user)):
    """
    Returns full course structure:
    { course, modules: [ {module, lessons, quiz} ] }
    """
    user_id = get_user_id(current_user)

    course = await _safe_one("SELECT * FROM courses WHERE id = :id", {"id": course_id})
    if not course:
        raise HTTPException(404, "Course not found")

    # Fetch modules
    modules_rows = await _safe(
        "SELECT * FROM course_modules WHERE course_id = :cid ORDER BY order_index, id",
        {"cid": course_id},
    )

    # Fetch completed lesson IDs for this user
    done_rows = await _safe(
        """
        SELECT lesson_id FROM user_lesson_progress
        WHERE user_id = :uid
        """,
        {"uid": user_id},
    )
    done_ids = {r["lesson_id"] for r in done_rows}

    modules_out = []
    for mod in modules_rows:
        mid = mod["id"]

        # Lessons under this module
        lessons_rows = await _safe(
            "SELECT * FROM lessons WHERE module_id = :mid ORDER BY order_index, id",
            {"mid": mid},
        )
        lessons_out = [
            {
                "id":               l["id"],
                "title":            l["title"],
                "content":          l.get("content", ""),
                "video_url":        l.get("video_url", ""),
                "duration_minutes": l.get("duration_minutes", 0),
                "order_index":      l.get("order_index", 0),
                "is_free_preview":  bool(l.get("is_free_preview", False)),
                "completed":        l["id"] in done_ids,
            }
            for l in lessons_rows
        ]

        # Quiz for this module (if any)
        quiz_row = await _safe_one(
            "SELECT id, title, pass_percentage, max_attempts FROM quizzes WHERE module_id = :mid",
            {"mid": mid},
        )
        quiz_out = None
        if quiz_row:
            q_count = await _safe_one(
                "SELECT COUNT(*) AS c FROM quiz_questions WHERE quiz_id = :qid",
                {"qid": quiz_row["id"]},
            )
            quiz_out = {
                "id":             quiz_row["id"],
                "title":          quiz_row["title"],
                "pass_percentage": quiz_row.get("pass_percentage", 70),
                "question_count": (q_count or {}).get("c", 0) if q_count else 0,
            }

        modules_out.append(
            {
                "id":          mid,
                "title":       mod["title"],
                "description": mod.get("description", ""),
                "order_index": mod.get("order_index", 0),
                "lessons":     lessons_out,
                "quiz":        quiz_out,
            }
        )

    # Also include lessons not attached to a module (order_index only)
    loose_rows = await _safe(
        "SELECT * FROM lessons WHERE course_id = :cid AND (module_id IS NULL) ORDER BY order_index, id",
        {"cid": course_id},
    )
    loose_out = [
        {
            "id":               l["id"],
            "title":            l["title"],
            "content":          l.get("content", ""),
            "video_url":        l.get("video_url", ""),
            "duration_minutes": l.get("duration_minutes", 0),
            "order_index":      l.get("order_index", 0),
            "is_free_preview":  bool(l.get("is_free_preview", False)),
            "completed":        l["id"] in done_ids,
        }
        for l in loose_rows
    ]

    return {
        "course":         _row(course),
        "modules":        modules_out,
        "loose_lessons":  loose_out,
    }


# ── Complete a lesson ─────────────────────────────────────────────────────────

@router.post("/{course_id}/lessons/{lesson_id}/complete")
async def complete_lesson(
    course_id: int,
    lesson_id: int,
    current_user=Depends(get_current_user),
):
    user_id = get_user_id(current_user)

    # Mark lesson as complete (UPSERT)
    try:
        await database.execute(
            """
            INSERT INTO user_lesson_progress (user_id, lesson_id, completed_at)
            VALUES (:uid, :lid, NOW())
            ON CONFLICT (user_id, lesson_id) DO NOTHING
            """,
            {"uid": user_id, "lid": lesson_id},
        )
    except Exception as e:
        raise HTTPException(500, f"Could not save progress: {e}")

    # Count total lessons in course and how many user has completed
    total_row = await _safe_one(
        "SELECT COUNT(*) AS c FROM lessons WHERE course_id = :cid AND COALESCE(is_active, TRUE) = TRUE",
        {"cid": course_id},
    )
    total_lessons = (total_row or {}).get("c", 1) or 1

    done_row = await _safe_one(
        """
        SELECT COUNT(*) AS c
        FROM user_lesson_progress ulp
        JOIN lessons l ON ulp.lesson_id = l.id
        WHERE ulp.user_id = :uid AND l.course_id = :cid
        """,
        {"uid": user_id, "cid": course_id},
    )
    completed = (done_row or {}).get("c", 0) or 0
    pct = min(100, int(completed / total_lessons * 100))

    # Upsert user_progress
    try:
        await database.execute(
            """
            INSERT INTO user_progress (user_id, course_id, progress_percent, completed_lessons, last_accessed)
            VALUES (:uid, :cid, :pct, :done, NOW())
            ON CONFLICT (user_id, course_id) DO UPDATE
                SET progress_percent  = EXCLUDED.progress_percent,
                    completed_lessons = EXCLUDED.completed_lessons,
                    last_accessed     = NOW(),
                    completed_at      = CASE WHEN EXCLUDED.progress_percent = 100 THEN NOW() ELSE user_progress.completed_at END
            """,
            {"uid": user_id, "cid": course_id, "pct": pct, "done": completed},
        )
    except Exception as e:
        print(f"[LMS] user_progress upsert error: {e}", flush=True)

    # Auto-issue certificate when course is 100% complete
    cert_issued = False
    cert_number = None
    if pct == 100:
        existing = await _safe_one(
            "SELECT id FROM certificates WHERE user_id = :uid AND course_id = :cid",
            {"uid": user_id, "cid": course_id},
        )
        if not existing:
            cert_number = f"PW-{course_id}-{user_id}-{uuid.uuid4().hex[:8].upper()}"
            try:
                await database.execute(
                    """
                    INSERT INTO certificates (user_id, course_id, certificate_number, issued_at)
                    VALUES (:uid, :cid, :num, NOW())
                    ON CONFLICT (user_id, course_id) DO NOTHING
                    """,
                    {"uid": user_id, "cid": course_id, "num": cert_number},
                )
                cert_issued = True
            except Exception as e:
                print(f"[LMS] certificate insert error: {e}", flush=True)

    return {
        "lesson_id":        lesson_id,
        "progress_percent": pct,
        "completed_lessons": completed,
        "total_lessons":    total_lessons,
        "course_complete":  pct == 100,
        "certificate_issued": cert_issued,
        "certificate_number": cert_number,
    }


# ── Quiz ──────────────────────────────────────────────────────────────────────

@router.get("/{course_id}/quizzes/{quiz_id}")
async def get_quiz(course_id: int, quiz_id: int, current_user=Depends(get_current_user)):
    quiz = await _safe_one(
        "SELECT id, title, pass_percentage, max_attempts FROM quizzes WHERE id = :qid",
        {"qid": quiz_id},
    )
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions = await _safe(
        """
        SELECT id, question, option_a, option_b,
               COALESCE(option_c, '') AS option_c,
               COALESCE(option_d, '') AS option_d,
               order_index
        FROM quiz_questions
        WHERE quiz_id = :qid
        ORDER BY order_index, id
        """,
        {"qid": quiz_id},
    )

    return {
        "id":              quiz["id"],
        "title":           quiz["title"],
        "pass_percentage": quiz.get("pass_percentage", 70),
        "max_attempts":    quiz.get("max_attempts", 3),
        "questions": [
            {
                "id":       q["id"],
                "question": q["question"],
                "options": {
                    "a": q["option_a"],
                    "b": q["option_b"],
                    "c": q.get("option_c", ""),
                    "d": q.get("option_d", ""),
                },
            }
            for q in questions
        ],
    }


@router.post("/{course_id}/quizzes/{quiz_id}/submit")
async def submit_quiz(
    course_id: int,
    quiz_id: int,
    answers: dict,               # {question_id: "a" | "b" | "c" | "d"}
    current_user=Depends(get_current_user),
):
    """
    Grade submitted quiz answers.
    answers: { "123": "a", "124": "c", ... }
    """
    user_id = get_user_id(current_user)

    quiz = await _safe_one(
        "SELECT id, pass_percentage FROM quizzes WHERE id = :qid",
        {"qid": quiz_id},
    )
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    pass_pct = quiz.get("pass_percentage", 70)

    questions = await _safe(
        "SELECT id, correct_option, explanation FROM quiz_questions WHERE quiz_id = :qid",
        {"qid": quiz_id},
    )
    if not questions:
        raise HTTPException(400, "Quiz has no questions")

    correct = 0
    breakdown = []
    for q in questions:
        qid    = str(q["id"])
        given  = (answers.get(qid) or "").lower().strip()
        answer = q["correct_option"].lower().strip()
        ok     = given == answer
        if ok:
            correct += 1
        breakdown.append({
            "question_id":    q["id"],
            "your_answer":    given,
            "correct_answer": answer,
            "correct":        ok,
            "explanation":    q.get("explanation", ""),
        })

    total  = len(questions)
    score  = round(correct / total * 100, 1) if total else 0
    passed = score >= pass_pct

    # Save attempt
    try:
        await database.execute(
            """
            INSERT INTO quiz_attempts (user_id, quiz_id, score, passed, answers, attempted_at)
            VALUES (:uid, :qid, :score, :passed, :answers, NOW())
            """,
            {
                "uid":     user_id,
                "qid":     quiz_id,
                "score":   score,
                "passed":  passed,
                "answers": json.dumps(answers),
            },
        )
    except Exception as e:
        print(f"[LMS] quiz_attempt save error: {e}", flush=True)

    return {
        "score":            score,
        "passed":           passed,
        "correct_answers":  correct,
        "total_questions":  total,
        "pass_percentage":  pass_pct,
        "results_breakdown": breakdown,
    }
