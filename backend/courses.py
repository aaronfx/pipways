"""
Courses + LMS API — Complete Rebuild
Endpoints:
  GET  /courses/list
  GET  /courses/{id}
  GET  /courses/{id}/curriculum
  POST /courses/{id}/lessons/{lesson_id}/complete
  GET  /courses/{id}/quizzes/{quiz_id}
  POST /courses/{id}/quizzes/{quiz_id}/submit
  GET  /courses/enhanced/progress
  GET  /courses/enhanced/certificate/{course_id}
"""
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from .database import database
from .security import get_current_user, get_user_id

router = APIRouter()


# ── db helpers ────────────────────────────────────────────────────────────────

async def _all(sql: str, params: dict = None) -> list:
    try:
        rows = await database.fetch_all(sql, params or {})
        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        print(f"[COURSES] _all error: {e}", flush=True)
        return []


async def _one(sql: str, params: dict = None) -> Optional[dict]:
    try:
        row = await database.fetch_one(sql, params or {})
        return dict(row) if row else None
    except Exception as e:
        print(f"[COURSES] _one error: {e}", flush=True)
        return None


async def _run(sql: str, params: dict = None):
    try:
        return await database.execute(sql, params or {})
    except Exception as e:
        print(f"[COURSES] _run error: {e}", flush=True)
        raise HTTPException(500, str(e))


# ── course listing ────────────────────────────────────────────────────────────

@router.get("/list")
async def list_courses(current_user=Depends(get_current_user)):
    user_id = get_user_id(current_user)

    # ── FIX: Use database.fetch_all() directly (not _all()) so that a query
    # failure CAN propagate to the except block.  Previously _all() caught ALL
    # exceptions internally and returned [], making the except fallback
    # unreachable — the same silent-failure bug that hit cms_list_courses.
    # ─────────────────────────────────────────────────────────────────────────
    rows = []
    try:
        raw = await database.fetch_all(
            """
            SELECT c.id, c.title, c.description, c.level,
                   -- FIX 9: Live COUNT instead of stale lesson_count column.
                   -- The column is never auto-updated when lessons are added via
                   -- the CMS, so it always reads 0.  A LEFT JOIN COUNT is the
                   -- only reliable source of truth.
                   COUNT(DISTINCT l.id)                        AS lesson_count,
                   COALESCE(c.thumbnail_url, c.thumbnail, '') AS thumbnail_url,
                   COALESCE(c.instructor, '')                  AS instructor,
                   COALESCE(up.progress_percent, 0)            AS progress,
                   COALESCE(up.completed_lessons, 0)           AS completed_lessons
            FROM courses c
            LEFT JOIN lessons l
                   ON l.course_id = c.id AND COALESCE(l.is_active, TRUE) = TRUE
            LEFT JOIN user_progress up
                   ON c.id = up.course_id AND up.user_id = :uid
            WHERE COALESCE(c.is_active, TRUE)     = TRUE
               OR COALESCE(c.is_published, FALSE) = TRUE
            GROUP BY c.id, c.title, c.description, c.level,
                     c.thumbnail_url, c.thumbnail, c.instructor,
                     up.progress_percent, up.completed_lessons
            ORDER BY c.created_at DESC
            """,
            {"uid": user_id},
        )
        rows = [dict(r) for r in raw] if raw else []
        print(f"[COURSES] list_courses (full): {len(rows)} rows", flush=True)
    except Exception as e:
        # Fallback: user_progress table / extra columns may not exist yet
        print(f"[COURSES] list_courses JOIN failed ({e}), using minimal fallback", flush=True)
        try:
            raw = await database.fetch_all(
                """
                SELECT id, title, description, level, created_at
                FROM courses
                WHERE COALESCE(is_active, TRUE)     = TRUE
                   OR COALESCE(is_published, FALSE) = TRUE
                ORDER BY created_at DESC
                """
            )
            # Inject defaults for columns that may not exist on older schemas
            rows = []
            for r in (raw or []):
                d = dict(r)
                d.setdefault("lesson_count", 0)
                d.setdefault("thumbnail_url", "")
                d.setdefault("instructor", "")
                d.setdefault("progress", 0)
                d.setdefault("completed_lessons", 0)
                rows.append(d)
            print(f"[COURSES] list_courses (minimal fallback): {len(rows)} rows", flush=True)
        except Exception as e2:
            print(f"[COURSES] list_courses CRITICAL: {e2}", flush=True)

    return [
        {
            "id":                r.get("id"),
            "title":             r.get("title", ""),
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


@router.get("/enhanced/progress")
async def get_progress(current_user=Depends(get_current_user)):
    user_id = get_user_id(current_user)

    rows = await _all(
        """
        SELECT c.id AS course_id, c.title,
               COALESCE(c.lesson_count, 0)            AS total_lessons,
               COALESCE(c.instructor, '')             AS instructor,
               COALESCE(c.thumbnail_url, c.thumbnail, '') AS thumbnail_url,
               COALESCE(up.progress_percent, 0)       AS progress_percent,
               COALESCE(up.completed_lessons, 0)      AS completed_lessons,
               up.completed_at, up.last_accessed
        FROM courses c
        LEFT JOIN user_progress up
               ON c.id = up.course_id AND up.user_id = :uid
        WHERE COALESCE(c.is_active, TRUE) = TRUE
           OR COALESCE(c.is_published, FALSE) = TRUE
        ORDER BY up.last_accessed DESC NULLS LAST
        """,
        {"uid": user_id},
    )

    in_progress, completed = [], []
    total_pct = 0

    for r in rows:
        pct = r.get("progress_percent", 0) or 0
        total_pct += pct
        entry = {
            "course_id":         r["course_id"],
            "title":             r["title"],
            "instructor":        r.get("instructor", ""),
            "thumbnail_url":     r.get("thumbnail_url", ""),
            "progress_percent":  pct,
            "completed_lessons": r.get("completed_lessons", 0),
            "total_lessons":     r.get("total_lessons", 0),
            "is_completed":      pct == 100,
            "last_accessed":     r["last_accessed"].isoformat() if r.get("last_accessed") else None,
            "completed_at":      r["completed_at"].isoformat()  if r.get("completed_at")  else None,
        }
        (completed if pct == 100 else in_progress).append(entry)

    user_row = await _one("SELECT full_name, email FROM users WHERE id=:uid", {"uid": user_id})
    student = (user_row or {}).get("full_name") or (user_row or {}).get("email", "Student") or "Student"

    cert_rows = await _all(
        """
        SELECT cert.certificate_number, cert.issued_at, c.title AS course_title
        FROM certificates cert JOIN courses c ON cert.course_id = c.id
        WHERE cert.user_id = :uid ORDER BY cert.issued_at DESC
        """,
        {"uid": user_id},
    )

    return {
        "in_progress":      in_progress,
        "completed":        completed,
        "certificates": [
            {
                "certificate_number": r["certificate_number"],
                "course_title":       r["course_title"],
                "student_name":       student,
                "issued_at":          r["issued_at"].isoformat() if r.get("issued_at") else None,
            }
            for r in cert_rows
        ],
        "overall_progress":  round(total_pct / len(rows)) if rows else 0,
        "total_courses":     len(rows),
        "completed_count":   len(completed),
        "student_name":      student,
    }


@router.get("/enhanced/certificate/{course_id}")
async def get_certificate(course_id: int, current_user=Depends(get_current_user)):
    user_id = get_user_id(current_user)
    row = await _one(
        """
        SELECT cert.certificate_number, cert.issued_at, c.title
        FROM certificates cert JOIN courses c ON cert.course_id = c.id
        WHERE cert.user_id=:uid AND cert.course_id=:cid
        """,
        {"uid": user_id, "cid": course_id},
    )
    if not row:
        raise HTTPException(404, "Certificate not found. Complete the course first.")
    user_row = await _one("SELECT full_name, email FROM users WHERE id=:uid", {"uid": user_id})
    student = (user_row or {}).get("full_name") or (user_row or {}).get("email", "Student") or "Student"
    return {
        "certificate_number": row["certificate_number"],
        "course_title":       row["title"],
        "student_name":       student,
        "issued_at":          row["issued_at"].isoformat() if row.get("issued_at") else None,
    }


@router.get("/{course_id}")
async def get_course(course_id: int, current_user=Depends(get_current_user)):
    row = await _one(
        "SELECT * FROM courses WHERE id=:id AND (COALESCE(is_active,TRUE)=TRUE OR COALESCE(is_published,FALSE)=TRUE)",
        {"id": course_id},
    )
    if not row:
        raise HTTPException(404, "Course not found")
    return row


@router.get("/{course_id}/curriculum")
async def get_curriculum(course_id: int, current_user=Depends(get_current_user)):
    user_id = get_user_id(current_user)

    course = await _one("SELECT * FROM courses WHERE id=:id", {"id": course_id})
    if not course:
        raise HTTPException(404, "Course not found")

    modules = await _all(
        "SELECT * FROM course_modules WHERE course_id=:cid ORDER BY order_index,id",
        {"cid": course_id},
    )

    done = {r["lesson_id"] for r in await _all(
        "SELECT lesson_id FROM user_lesson_progress WHERE user_id=:uid", {"uid": user_id}
    )}

    def fmt_lesson(l: dict) -> dict:
        return {
            "id":               l["id"],
            "title":            l["title"],
            "content":          l.get("content", ""),
            "video_url":        l.get("video_url", ""),
            "duration_minutes": l.get("duration_minutes", 0),
            "order_index":      l.get("order_index", 0),
            "is_free_preview":  bool(l.get("is_free_preview", False)),
            "completed":        l["id"] in done,
        }

    mods_out = []
    for mod in modules:
        lessons = await _all(
            "SELECT * FROM lessons WHERE module_id=:mid ORDER BY order_index,id",
            {"mid": mod["id"]},
        )
        quiz = await _one(
            "SELECT id, title, pass_percentage, max_attempts FROM quizzes WHERE module_id=:mid",
            {"mid": mod["id"]},
        )
        qcount = (await _one(
            "SELECT COUNT(*) AS c FROM quiz_questions WHERE quiz_id=:qid",
            {"qid": quiz["id"]},
        ) or {}).get("c", 0) if quiz else 0
        mods_out.append({
            "id":          mod["id"],
            "title":       mod["title"],
            "description": mod.get("description", ""),
            "order_index": mod.get("order_index", 0),
            "lessons":     [fmt_lesson(l) for l in lessons],
            "quiz":        {**quiz, "question_count": qcount} if quiz else None,
        })

    loose = await _all(
        "SELECT * FROM lessons WHERE course_id=:cid AND module_id IS NULL ORDER BY order_index,id",
        {"cid": course_id},
    )

    return {
        "course":        dict(course),
        "modules":       mods_out,
        "loose_lessons": [fmt_lesson(l) for l in loose],
    }


@router.post("/{course_id}/lessons/{lesson_id}/complete")
async def complete_lesson(course_id: int, lesson_id: int, current_user=Depends(get_current_user)):
    user_id = get_user_id(current_user)

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

    total_row = await _one(
        "SELECT COUNT(*) AS c FROM lessons WHERE course_id=:cid AND COALESCE(is_active,TRUE)=TRUE",
        {"cid": course_id},
    )
    total = max((total_row or {}).get("c", 1) or 1, 1)

    done_row = await _one(
        """
        SELECT COUNT(*) AS c FROM user_lesson_progress ulp
        JOIN lessons l ON ulp.lesson_id = l.id
        WHERE ulp.user_id=:uid AND l.course_id=:cid
        """,
        {"uid": user_id, "cid": course_id},
    )
    done = (done_row or {}).get("c", 0) or 0
    pct  = min(100, int(done / total * 100))

    try:
        await database.execute(
            """
            INSERT INTO user_progress (user_id, course_id, progress_percent, completed_lessons, last_accessed)
            VALUES (:uid, :cid, :pct, :done, NOW())
            ON CONFLICT (user_id, course_id) DO UPDATE
                SET progress_percent  = EXCLUDED.progress_percent,
                    completed_lessons = EXCLUDED.completed_lessons,
                    last_accessed     = NOW(),
                    completed_at      = CASE WHEN EXCLUDED.progress_percent = 100 THEN NOW()
                                             ELSE user_progress.completed_at END
            """,
            {"uid": user_id, "cid": course_id, "pct": pct, "done": done},
        )
    except Exception as e:
        print(f"[COURSES] progress upsert error: {e}", flush=True)

    cert_number = None
    cert_issued = False
    if pct == 100:
        existing = await _one(
            "SELECT id FROM certificates WHERE user_id=:uid AND course_id=:cid",
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
                print(f"[COURSES] cert error: {e}", flush=True)

    return {
        "lesson_id":          lesson_id,
        "progress_percent":   pct,
        "completed_lessons":  done,
        "total_lessons":      total,
        "course_complete":    pct == 100,
        "certificate_issued": cert_issued,
        "certificate_number": cert_number,
    }


@router.get("/{course_id}/quizzes/{quiz_id}")
async def get_quiz(course_id: int, quiz_id: int, current_user=Depends(get_current_user)):
    quiz = await _one(
        "SELECT id, title, pass_percentage, max_attempts FROM quizzes WHERE id=:qid",
        {"qid": quiz_id},
    )
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions = await _all(
        """
        SELECT id, question, option_a, option_b,
               COALESCE(option_c,'') AS option_c,
               COALESCE(option_d,'') AS option_d,
               order_index
        FROM quiz_questions WHERE quiz_id=:qid ORDER BY order_index,id
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
                "options": {"a": q["option_a"], "b": q["option_b"],
                            "c": q.get("option_c",""), "d": q.get("option_d","")},
            }
            for q in questions
        ],
    }


@router.post("/{course_id}/quizzes/{quiz_id}/submit")
async def submit_quiz(
    course_id: int,
    quiz_id:   int,
    answers:   dict,
    current_user=Depends(get_current_user),
):
    user_id = get_user_id(current_user)
    quiz = await _one("SELECT pass_percentage FROM quizzes WHERE id=:qid", {"qid": quiz_id})
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    questions = await _all(
        "SELECT id, correct_option, explanation FROM quiz_questions WHERE quiz_id=:qid",
        {"qid": quiz_id},
    )
    if not questions:
        raise HTTPException(400, "Quiz has no questions")

    correct, breakdown = 0, []
    for q in questions:
        given  = (answers.get(str(q["id"])) or "").lower().strip()
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
    passed = score >= quiz.get("pass_percentage", 70)

    try:
        await database.execute(
            """
            INSERT INTO quiz_attempts (user_id, quiz_id, score, passed, answers, attempted_at)
            VALUES (:uid, :qid, :score, :passed, :answers, NOW())
            """,
            {"uid": user_id, "qid": quiz_id, "score": score,
             "passed": passed, "answers": json.dumps(answers)},
        )
    except Exception as e:
        print(f"[COURSES] quiz attempt save error: {e}", flush=True)

    return {
        "score":             score,
        "passed":            passed,
        "correct_answers":   correct,
        "total_questions":   total,
        "pass_percentage":   quiz.get("pass_percentage", 70),
        "results_breakdown": breakdown,
    }
