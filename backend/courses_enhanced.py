"""
Courses Enhanced API - Progress dashboard & certificate generation.
Endpoints:
  GET /courses/enhanced/progress
  GET /courses/enhanced/certificate/{course_id}
"""
from fastapi import APIRouter, Depends, HTTPException
from .database import database
from .security import get_current_user, get_user_id

router = APIRouter()


async def _safe_all(q: str, params: dict = None):
    try:
        return await database.fetch_all(q, params or {})
    except Exception:
        return []


async def _safe_one(q: str, params: dict = None):
    try:
        return await database.fetch_one(q, params or {})
    except Exception:
        return None


@router.get("/enhanced/progress")
async def get_progress(current_user=Depends(get_current_user)):
    """
    Returns a complete learning dashboard for the current user:
    - courses in progress
    - completed courses
    - certificates earned
    - overall progress percentage
    """
    user_id = get_user_id(current_user)

    rows = await _safe_all(
        """
        SELECT
            c.id   AS course_id,
            c.title,
            COALESCE(c.lesson_count, 0)      AS total_lessons,
            COALESCE(c.instructor, '')        AS instructor,
            COALESCE(c.thumbnail_url, c.thumbnail, '') AS thumbnail_url,
            COALESCE(up.progress_percent, 0) AS progress_percent,
            COALESCE(up.completed_lessons, 0) AS completed_lessons,
            up.completed_at,
            up.last_accessed
        FROM courses c
        LEFT JOIN user_progress up
               ON c.id = up.course_id AND up.user_id = :uid
        WHERE COALESCE(c.is_active, TRUE) = TRUE
           OR COALESCE(c.is_published, FALSE) = TRUE
        ORDER BY up.last_accessed DESC NULLS LAST
        """,
        {"uid": user_id},
    )

    in_progress  = []
    completed    = []
    total_pct_sum = 0

    for r in rows:
        pct     = r.get("progress_percent", 0) or 0
        is_done = pct == 100
        total_pct_sum += pct

        entry = {
            "course_id":        r["course_id"],
            "title":            r["title"],
            "instructor":       r.get("instructor", ""),
            "thumbnail_url":    r.get("thumbnail_url", ""),
            "progress_percent": pct,
            "completed_lessons": r.get("completed_lessons", 0),
            "total_lessons":    r.get("total_lessons", 0),
            "is_completed":     is_done,
            "last_accessed":    r["last_accessed"].isoformat() if r.get("last_accessed") else None,
            "completed_at":     r["completed_at"].isoformat()  if r.get("completed_at")  else None,
        }
        (completed if is_done else in_progress).append(entry)

    # Certificates
    cert_rows = await _safe_all(
        """
        SELECT cert.certificate_number, cert.issued_at,
               c.title AS course_title
        FROM certificates cert
        JOIN courses c ON cert.course_id = c.id
        WHERE cert.user_id = :uid
        ORDER BY cert.issued_at DESC
        """,
        {"uid": user_id},
    )

    # User full name for certificate display
    user_row = await _safe_one("SELECT full_name, email FROM users WHERE id = :uid", {"uid": user_id})
    student_name = (user_row or {}).get("full_name") or (user_row or {}).get("email", "Student") or "Student"

    certificates = [
        {
            "certificate_number": r["certificate_number"],
            "course_title":       r["course_title"],
            "student_name":       student_name,
            "issued_at":          r["issued_at"].isoformat() if r.get("issued_at") else None,
        }
        for r in cert_rows
    ]

    total_courses = len(rows)
    overall_pct   = round(total_pct_sum / total_courses) if total_courses else 0

    return {
        "in_progress":       in_progress,
        "completed":         completed,
        "certificates":      certificates,
        "overall_progress":  overall_pct,
        "total_courses":     total_courses,
        "completed_count":   len(completed),
        "student_name":      student_name,
    }


@router.get("/enhanced/certificate/{course_id}")
async def get_certificate(course_id: int, current_user=Depends(get_current_user)):
    """
    Retrieve certificate details for a specific completed course.
    """
    user_id = get_user_id(current_user)

    row = await _safe_one(
        """
        SELECT cert.certificate_number, cert.issued_at,
               c.title AS course_title
        FROM certificates cert
        JOIN courses c ON cert.course_id = c.id
        WHERE cert.user_id = :uid AND cert.course_id = :cid
        """,
        {"uid": user_id, "cid": course_id},
    )
    if not row:
        raise HTTPException(404, "Certificate not found. Complete the course first.")

    user_row = await _safe_one("SELECT full_name, email FROM users WHERE id = :uid", {"uid": user_id})
    student_name = (user_row or {}).get("full_name") or (user_row or {}).get("email", "Student") or "Student"

    return {
        "certificate_number": row["certificate_number"],
        "course_title":       row["course_title"],
        "student_name":       student_name,
        "issued_at":          row["issued_at"].isoformat() if row.get("issued_at") else None,
        "course_id":          course_id,
    }
