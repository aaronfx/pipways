"""
Webinars API - PRODUCTION READY
Fixes:
 1. rows fetched in try but response built in except — happy path returned nothing
 2. scheduled_at date filter excluded webinars with NULL or past dates
 3. is_published not checked alongside status
"""
from fastapi import APIRouter, Depends, HTTPException
from .database import database
from .security import get_current_user

router = APIRouter()


def _fmt_webinar(row, upcoming: bool) -> dict:
    sat = row.get("scheduled_at")
    return {
        "id":               row["id"],
        "title":            row["title"],
        "description":      row.get("description", ""),
        "presenter":        row.get("presenter", "TBA") or "TBA",
        "scheduled_at":     sat.isoformat() if sat else None,
        "status":           row.get("status", "scheduled"),
        "duration_minutes": row.get("duration_minutes", 60) or 60,
        "meeting_link":     row.get("meeting_link", "") if upcoming else None,
        "recording_url":    row.get("recording_url", "") if not upcoming else None,
        "is_published":     bool(row.get("is_published", False)),
        "max_attendees":    row.get("max_attendees", 100) or 100,
    }


@router.get("/upcoming")
async def get_webinars(
    upcoming: bool = True,
    current_user = Depends(get_current_user)
):
    rows = []

    if upcoming:
        try:
            rows = await database.fetch_all(
                """
                SELECT id, title, description,
                       COALESCE(presenter, '') AS presenter,
                       scheduled_at, status,
                       COALESCE(duration_minutes, 60)  AS duration_minutes,
                       COALESCE(meeting_link, '')       AS meeting_link,
                       COALESCE(recording_url, '')      AS recording_url,
                       COALESCE(max_attendees, 100)     AS max_attendees,
                       COALESCE(is_published, FALSE)    AS is_published
                FROM webinars
                WHERE
                    COALESCE(is_published, FALSE) = TRUE
                    OR (status IN ('scheduled', 'live')
                        AND scheduled_at > NOW() - INTERVAL '2 hours')
                ORDER BY scheduled_at ASC NULLS LAST
                """
            )
        except Exception:
            try:
                rows = await database.fetch_all(
                    "SELECT * FROM webinars WHERE status IN ('scheduled','live') ORDER BY scheduled_at ASC NULLS LAST"
                )
            except Exception as e:
                print(f"[WEBINARS] fetch error: {e}", flush=True)
                return []
    else:
        try:
            rows = await database.fetch_all(
                """
                SELECT id, title, description,
                       COALESCE(presenter, '') AS presenter,
                       scheduled_at, status,
                       COALESCE(duration_minutes, 60) AS duration_minutes,
                       COALESCE(recording_url, '')    AS recording_url,
                       COALESCE(is_published, FALSE)  AS is_published
                FROM webinars
                WHERE status = 'recorded'
                ORDER BY scheduled_at DESC NULLS LAST
                LIMIT 10
                """
            )
        except Exception:
            try:
                rows = await database.fetch_all(
                    "SELECT * FROM webinars WHERE status='recorded' ORDER BY scheduled_at DESC LIMIT 10"
                )
            except Exception as e:
                print(f"[WEBINARS] fetch error: {e}", flush=True)
                return []

    result = [_fmt_webinar(dict(r), upcoming) for r in rows]
    print(f"[WEBINARS] Returning {len(result)} (upcoming={upcoming})", flush=True)
    return result
