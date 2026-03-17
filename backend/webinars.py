"""
Webinars API — Complete Rebuild
Endpoints:
  GET /webinars/upcoming?upcoming=true|false

Design decisions:
- status field uses LOWER() comparisons — no case sensitivity issues
- is_published checked as OR condition — CMS toggle always works
- No hard date cutoff for published webinars — show them regardless of date
- Returns all fields the frontend and CMS js expect
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from .database import database
from .security import get_current_user

router = APIRouter()


async def _fetch(sql: str, params: dict = None) -> list:
    try:
        rows = await database.fetch_all(sql, params or {})
        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        print(f"[WEBINARS] query error: {e}", flush=True)
        return []


def _fmt(row: dict, upcoming: bool) -> dict:
    sat = row.get("scheduled_at")
    return {
        "id":               row.get("id"),
        "title":            row.get("title", ""),
        "description":      row.get("description", "") or "",
        "presenter":        row.get("presenter", "") or "TBA",
        "scheduled_at":     sat.isoformat() if sat else None,
        "status":           row.get("status", "scheduled"),
        "duration_minutes": row.get("duration_minutes") or 60,
        "meeting_link":     (row.get("meeting_link") or "") if upcoming else None,
        "recording_url":    (row.get("recording_url") or "") if not upcoming else None,
        "is_published":     bool(row.get("is_published", False)),
        "max_attendees":    row.get("max_attendees") or 100,
        "thumbnail":        row.get("thumbnail") or "",
    }


@router.get("/upcoming")
async def get_webinars(
    upcoming: bool = True,
    current_user=Depends(get_current_user),
):
    """
    Fetch webinars for the public page.
    - upcoming=true  → published or scheduled/live
    - upcoming=false → recorded only

    Two-stage query: rich columns first, plain fallback if columns missing.
    """
    if upcoming:
        # Stage 1: try with all new columns
        rows = await _fetch(
            """
            SELECT id, title, description,
                   COALESCE(presenter, '')        AS presenter,
                   scheduled_at,
                   COALESCE(status, 'scheduled')  AS status,
                   COALESCE(duration_minutes, 60) AS duration_minutes,
                   COALESCE(meeting_link, '')      AS meeting_link,
                   COALESCE(recording_url, '')     AS recording_url,
                   COALESCE(max_attendees, 100)    AS max_attendees,
                   COALESCE(is_published, FALSE)   AS is_published,
                   COALESCE(thumbnail, '')         AS thumbnail
            FROM webinars
            WHERE COALESCE(is_published, FALSE) = TRUE
               OR LOWER(COALESCE(status, '')) IN ('scheduled', 'live')
            ORDER BY scheduled_at ASC NULLS LAST
            """
        )

        # Stage 2: simple fallback if new columns don't exist
        if not rows:
            rows = await _fetch(
                """
                SELECT id, title, description, presenter,
                       scheduled_at, status, duration_minutes,
                       meeting_link, recording_url
                FROM webinars
                WHERE LOWER(COALESCE(status, '')) IN ('scheduled', 'live', 'published')
                ORDER BY scheduled_at ASC NULLS LAST
                """
            )
    else:
        rows = await _fetch(
            """
            SELECT id, title, description,
                   COALESCE(presenter, '')        AS presenter,
                   scheduled_at,
                   COALESCE(status, 'recorded')   AS status,
                   COALESCE(duration_minutes, 60) AS duration_minutes,
                   COALESCE(recording_url, '')     AS recording_url,
                   COALESCE(is_published, FALSE)   AS is_published
            FROM webinars
            WHERE LOWER(COALESCE(status, '')) = 'recorded'
            ORDER BY scheduled_at DESC NULLS LAST
            LIMIT 20
            """
        )
        if not rows:
            rows = await _fetch(
                "SELECT * FROM webinars WHERE LOWER(COALESCE(status,'')) = 'recorded' "
                "ORDER BY scheduled_at DESC LIMIT 20"
            )

    result = [_fmt(r, upcoming) for r in rows]
    print(f"[WEBINARS] /upcoming?upcoming={upcoming} → {len(result)} records", flush=True)
    return result
