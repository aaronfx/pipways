"""
Webinars API — v2 Session Hub Upgrade
New columns : youtube_url, embed_url
New endpoints:
  POST /webinars/{id}/register     — user self-registration
  GET  /webinars/{id}/registrants  — admin only, attendee list
  GET  /webinars/{id}/my-registration — check if current user is registered
"""
from typing import Optional

# ── Auto-migration: new columns added if missing (idempotent) ────────────────
_WEBINAR_NEW_COLS = [
    "ALTER TABLE webinars ADD COLUMN IF NOT EXISTS speaker_bio TEXT DEFAULT ''",
    "ALTER TABLE webinars ADD COLUMN IF NOT EXISTS tags VARCHAR(500) DEFAULT ''",
    # v2 Session Hub
    "ALTER TABLE webinars ADD COLUMN IF NOT EXISTS youtube_url VARCHAR(500) DEFAULT ''",
    "ALTER TABLE webinars ADD COLUMN IF NOT EXISTS embed_url VARCHAR(500) DEFAULT ''",
]

_REGISTRATION_TABLE = """
CREATE TABLE IF NOT EXISTS webinar_registrations (
    id            SERIAL PRIMARY KEY,
    webinar_id    INTEGER NOT NULL,
    user_id       INTEGER NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(webinar_id, user_id)
)
"""

from fastapi import APIRouter, Depends, HTTPException
from .database import database
from .security import get_current_user
from .email_service import send_webinar_confirmation_task

router = APIRouter()


# ── Internal helpers ─────────────────────────────────────────────────────────

async def _fetch(sql: str, params: dict = None) -> list:
    try:
        rows = await database.fetch_all(sql, params or {})
        return [dict(r) for r in rows] if rows else []
    except Exception as e:
        print(f"[WEBINARS] query error: {e}", flush=True)
        return []


def _fmt(row: dict, upcoming: bool) -> dict:
    sat    = row.get("scheduled_at")
    status = (row.get("status") or "scheduled").lower()
    now    = __import__("datetime").datetime.utcnow()

    is_past      = sat and sat < now
    is_completed = is_past and status in ("scheduled", "live", "published", "completed")
    if is_completed:
        status = "completed"

    return {
        "id":               row.get("id"),
        "title":            row.get("title", ""),
        "description":      row.get("description", "") or "",
        "presenter":        row.get("presenter", "") or "TBA",
        "speaker_bio":      row.get("speaker_bio", "") or "",
        "scheduled_at":     sat.isoformat() if sat else None,
        "status":           status,
        "is_completed":     is_completed,
        "duration_minutes": row.get("duration_minutes") or 60,
        "meeting_link":     (row.get("meeting_link") or "") if not is_completed else "",
        "recording_url":    row.get("recording_url") or "",
        "youtube_url":      row.get("youtube_url") or "",
        "embed_url":        row.get("embed_url") or "",
        "is_published":     bool(row.get("is_published", False)),
        "max_attendees":    row.get("max_attendees") or 100,
        "thumbnail":        row.get("thumbnail") or "",
        "tags":             row.get("tags") or "",
    }


async def _run_webinar_migrations():
    for sql in _WEBINAR_NEW_COLS:
        try:
            await database.execute(sql)
        except Exception:
            pass
    try:
        await database.execute(_REGISTRATION_TABLE)
    except Exception as e:
        print(f"[WEBINARS] registration table migration error: {e}", flush=True)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/upcoming")
async def get_webinars(
    upcoming: bool = True,
    current_user=Depends(get_current_user),
):
    """
    Fetch webinars for the session hub.
    - upcoming=true  → published or scheduled/live (+ completed for past recordings tab)
    - upcoming=false → recorded only
    """
    await _run_webinar_migrations()

    if upcoming:
        rows = await _fetch(
            """
            SELECT id, title, description,
                   COALESCE(presenter, '')          AS presenter,
                   COALESCE(speaker_bio, '')        AS speaker_bio,
                   scheduled_at,
                   COALESCE(status, 'scheduled')    AS status,
                   COALESCE(duration_minutes, 60)   AS duration_minutes,
                   COALESCE(meeting_link, '')        AS meeting_link,
                   COALESCE(recording_url, '')       AS recording_url,
                   COALESCE(youtube_url, '')         AS youtube_url,
                   COALESCE(embed_url, '')           AS embed_url,
                   COALESCE(max_attendees, 100)      AS max_attendees,
                   COALESCE(is_published, FALSE)     AS is_published,
                   COALESCE(thumbnail, '')           AS thumbnail,
                   COALESCE(tags, '')                AS tags
            FROM webinars
            WHERE COALESCE(is_published, FALSE) = TRUE
               OR LOWER(COALESCE(status, '')) IN ('scheduled', 'live', 'completed')
            ORDER BY scheduled_at ASC NULLS LAST
            """
        )
        if not rows:
            rows = await _fetch(
                """
                SELECT id, title, description, presenter,
                       scheduled_at, status, duration_minutes,
                       meeting_link, recording_url
                FROM webinars
                WHERE LOWER(COALESCE(status, '')) IN ('scheduled', 'live', 'published', 'completed')
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
                   COALESCE(youtube_url, '')       AS youtube_url,
                   COALESCE(embed_url, '')         AS embed_url,
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


@router.post("/{webinar_id}/register")
async def register_for_webinar(
    webinar_id: int,
    current_user=Depends(get_current_user),
):
    """
    Register the authenticated user for a webinar.
    Idempotent — re-registering returns success without error.
    """
    await _run_webinar_migrations()

    # Fetch the full webinar row — include all fields needed for the confirmation email
    webinar = await _fetch(
        """
        SELECT id, title, max_attendees,
               scheduled_at,
               COALESCE(presenter, '')        AS presenter,
               COALESCE(duration_minutes, 60) AS duration_minutes
        FROM webinars WHERE id = :id
        """,
        {"id": webinar_id}
    )
    if not webinar:
        raise HTTPException(status_code=404, detail="Webinar not found")

    # Check capacity
    w = webinar[0]
    count_rows = await _fetch(
        "SELECT COUNT(*) AS cnt FROM webinar_registrations WHERE webinar_id = :wid",
        {"wid": webinar_id}
    )
    current_count = count_rows[0]["cnt"] if count_rows else 0
    max_att = w.get("max_attendees") or 100

    if current_count >= max_att:
        raise HTTPException(status_code=400, detail="This session is fully booked")

    # Insert — ignore duplicate (ON CONFLICT DO NOTHING)
    try:
        await database.execute(
            """
            INSERT INTO webinar_registrations (webinar_id, user_id)
            VALUES (:wid, :uid)
            ON CONFLICT (webinar_id, user_id) DO NOTHING
            """,
            {"wid": webinar_id, "uid": current_user["id"]}
        )
    except Exception as e:
        print(f"[WEBINARS] registration insert error: {e}", flush=True)
        raise HTTPException(status_code=500, detail="Registration failed")

    print(f"[WEBINARS] user {current_user['id']} registered for webinar {webinar_id} "
          f"(scheduled_at={w.get('scheduled_at')})", flush=True)

    # ── Send confirmation email (fire-and-forget, non-blocking) ─────────────
    try:
        user_row = await database.fetch_one(
            "SELECT email, full_name FROM users WHERE id = :uid",
            {"uid": current_user["id"]}
        )
        if user_row:
            import asyncio
            asyncio.create_task(send_webinar_confirmation_task(
                user_id          = current_user["id"],
                email            = user_row["email"],
                full_name        = user_row["full_name"] or "Trader",
                session_title    = w["title"],
                presenter        = w.get("presenter") or "",
                scheduled_at     = w.get("scheduled_at"),   # now always populated
                duration_minutes = w.get("duration_minutes") or 60,
                webinar_id       = webinar_id,               # fallback for email_service
            ))
    except Exception as e:
        print(f"[WEBINARS] Confirmation email error (non-blocking): {e}", flush=True)

    return {
        "success": True,
        "message": f"You're registered for \"{w['title']}\". Check your email for confirmation.",
        "webinar_id": webinar_id,
    }


@router.get("/{webinar_id}/my-registration")
async def my_registration(
    webinar_id: int,
    current_user=Depends(get_current_user),
):
    """Check whether the current user is already registered."""
    await _run_webinar_migrations()
    rows = await _fetch(
        "SELECT id FROM webinar_registrations WHERE webinar_id = :wid AND user_id = :uid",
        {"wid": webinar_id, "uid": current_user["id"]}
    )
    return {"registered": bool(rows)}


@router.get("/{webinar_id}/registrants")
async def get_registrants(
    webinar_id: int,
    current_user=Depends(get_current_user),
):
    """Admin only — list all registrants for a webinar."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    await _run_webinar_migrations()
    rows = await _fetch(
        """
        SELECT wr.id, wr.registered_at,
               u.email, u.full_name
        FROM webinar_registrations wr
        JOIN users u ON u.id = wr.user_id
        WHERE wr.webinar_id = :wid
        ORDER BY wr.registered_at ASC
        """,
        {"wid": webinar_id}
    )
    return {"webinar_id": webinar_id, "count": len(rows), "registrants": rows}
