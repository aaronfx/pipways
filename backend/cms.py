"""
CMS API — Admin-only CRUD for Blog, Courses/LMS, Signals, Webinars, Site Settings
All endpoints are protected by the admin guard imported from admin.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import json

from .admin import get_admin_user
from .database import database

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt(v) -> str:
    if isinstance(v, (datetime,)): return v.isoformat()
    return str(v) if v is not None else ""

async def _row(query: str, values: dict = None):
    try:
        r = await database.fetch_one(query, values or {})
        return dict(r) if r else None
    except Exception as e:
        print(f"[CMS] row error: {e}", flush=True)
        return None

async def _rows(query: str, values: dict = None):
    try:
        rs = await database.fetch_all(query, values or {})
        return [dict(r) for r in rs] if rs else []
    except Exception as e:
        print(f"[CMS] rows error: {e}", flush=True)
        return []

async def _exec(query: str, values: dict = None):
    try:
        return await database.execute(query, values or {})
    except Exception as e:
        print(f"[CMS] exec error: {e}", flush=True)
        raise HTTPException(500, f"Database error: {str(e)}")

def _safe_tags(tags_input) -> str:
    """Normalise tags to a JSON string for storage."""
    if isinstance(tags_input, list):
        return json.dumps(tags_input)
    if isinstance(tags_input, str):
        try:
            json.loads(tags_input)   # already valid JSON
            return tags_input
        except Exception:
            return json.dumps([t.strip() for t in tags_input.split(",") if t.strip()])
    return "[]"

def _parse_tags(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return [t.strip() for t in str(raw).split(",") if t.strip()]


# ══════════════════════════════════════════════════════════════════════════════
# BLOG
# ══════════════════════════════════════════════════════════════════════════════

class BlogPostIn(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = ""
    content: str
    category: Optional[str] = "General"
    tags: Optional[Any] = []
    featured_image: Optional[str] = ""
    is_published: bool = False

@router.get("/blog")
async def cms_list_posts(_=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT id, title, slug, excerpt, category, tags, featured_image, "
        "is_published, views, created_at, updated_at "
        "FROM blog_posts ORDER BY created_at DESC"
    )
    for r in rows:
        r["tags"]       = _parse_tags(r.get("tags"))
        r["created_at"] = _fmt(r.get("created_at"))
        r["updated_at"] = _fmt(r.get("updated_at"))
    return rows

@router.get("/blog/{post_id}")
async def cms_get_post(post_id: int, _=Depends(get_admin_user)):
    r = await _row("SELECT * FROM blog_posts WHERE id = :id", {"id": post_id})
    if not r:
        raise HTTPException(404, "Post not found")
    r["tags"] = _parse_tags(r.get("tags"))
    return r

@router.post("/blog", status_code=201)
async def cms_create_post(data: BlogPostIn, _=Depends(get_admin_user)):
    # Check slug uniqueness
    existing = await _row("SELECT id FROM blog_posts WHERE slug = :slug", {"slug": data.slug})
    if existing:
        raise HTTPException(400, f"Slug '{data.slug}' already exists")
    now = datetime.utcnow()
    post_id = await _exec(
        "INSERT INTO blog_posts (title, slug, excerpt, content, category, tags, "
        "featured_image, is_published, views, created_at, updated_at) "
        "VALUES (:title,:slug,:excerpt,:content,:category,:tags,:img,:pub,0,:now,:now)",
        {"title": data.title, "slug": data.slug, "excerpt": data.excerpt or "",
         "content": data.content, "category": data.category or "General",
         "tags": _safe_tags(data.tags), "img": data.featured_image or "",
         "pub": data.is_published, "now": now}
    )
    return {"id": post_id, "message": "Post created"}

@router.put("/blog/{post_id}")
async def cms_update_post(post_id: int, data: BlogPostIn, _=Depends(get_admin_user)):
    existing = await _row("SELECT id FROM blog_posts WHERE id = :id", {"id": post_id})
    if not existing:
        raise HTTPException(404, "Post not found")
    await _exec(
        "UPDATE blog_posts SET title=:title, slug=:slug, excerpt=:excerpt, content=:content, "
        "category=:category, tags=:tags, featured_image=:img, is_published=:pub, "
        "updated_at=:now WHERE id=:id",
        {"title": data.title, "slug": data.slug, "excerpt": data.excerpt or "",
         "content": data.content, "category": data.category or "General",
         "tags": _safe_tags(data.tags), "img": data.featured_image or "",
         "pub": data.is_published, "now": datetime.utcnow(), "id": post_id}
    )
    return {"message": "Post updated"}

@router.delete("/blog/{post_id}")
async def cms_delete_post(post_id: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM blog_posts WHERE id = :id", {"id": post_id})
    return {"message": "Post deleted"}

@router.post("/blog/{post_id}/toggle-publish")
async def cms_toggle_post(post_id: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id, is_published FROM blog_posts WHERE id = :id", {"id": post_id})
    if not r:
        raise HTTPException(404, "Post not found")
    new_state = not bool(r["is_published"])
    await _exec("UPDATE blog_posts SET is_published=:pub, updated_at=:now WHERE id=:id",
                {"pub": new_state, "now": datetime.utcnow(), "id": post_id})
    return {"is_published": new_state, "message": "Published" if new_state else "Unpublished"}


# ══════════════════════════════════════════════════════════════════════════════
# COURSES / LMS
# ══════════════════════════════════════════════════════════════════════════════

class CourseIn(BaseModel):
    title: str
    description: Optional[str] = ""
    level: Optional[str] = "Beginner"
    price: Optional[float] = 0.0
    thumbnail: Optional[str] = ""
    is_published: bool = False

class LessonIn(BaseModel):
    course_id: int
    title: str
    content: Optional[str] = ""
    video_url: Optional[str] = ""
    duration_minutes: Optional[int] = 0
    order_index: Optional[int] = 0

@router.get("/courses")
async def cms_list_courses(_=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT c.id, c.title, c.description, c.level, c.price, c.thumbnail, "
        "c.is_published, c.created_at, "
        "COUNT(l.id) AS lesson_count "
        "FROM courses c LEFT JOIN lessons l ON l.course_id = c.id "
        "GROUP BY c.id ORDER BY c.created_at DESC"
    )
    for r in rows:
        r["created_at"]   = _fmt(r.get("created_at"))
        r["lesson_count"] = r.get("lesson_count") or 0
    return rows

@router.get("/courses/{course_id}/lessons")
async def cms_list_lessons(course_id: int, _=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT * FROM lessons WHERE course_id = :cid ORDER BY order_index, id",
        {"cid": course_id}
    )
    for r in rows:
        r["created_at"] = _fmt(r.get("created_at"))
    return rows

@router.post("/courses", status_code=201)
async def cms_create_course(data: CourseIn, _=Depends(get_admin_user)):
    now = datetime.utcnow()
    cid = await _exec(
        "INSERT INTO courses (title, description, level, price, thumbnail, is_published, created_at) "
        "VALUES (:title,:desc,:level,:price,:thumb,:pub,:now)",
        {"title": data.title, "desc": data.description or "", "level": data.level or "Beginner",
         "price": data.price or 0.0, "thumb": data.thumbnail or "",
         "pub": data.is_published, "now": now}
    )
    return {"id": cid, "message": "Course created"}

@router.put("/courses/{course_id}")
async def cms_update_course(course_id: int, data: CourseIn, _=Depends(get_admin_user)):
    existing = await _row("SELECT id FROM courses WHERE id = :id", {"id": course_id})
    if not existing:
        raise HTTPException(404, "Course not found")
    await _exec(
        "UPDATE courses SET title=:title, description=:desc, level=:level, price=:price, "
        "thumbnail=:thumb, is_published=:pub WHERE id=:id",
        {"title": data.title, "desc": data.description or "", "level": data.level or "Beginner",
         "price": data.price or 0.0, "thumb": data.thumbnail or "",
         "pub": data.is_published, "id": course_id}
    )
    return {"message": "Course updated"}

@router.delete("/courses/{course_id}")
async def cms_delete_course(course_id: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM lessons WHERE course_id = :id", {"id": course_id})
    await _exec("DELETE FROM courses WHERE id = :id", {"id": course_id})
    return {"message": "Course and lessons deleted"}

@router.post("/courses/{course_id}/toggle-publish")
async def cms_toggle_course(course_id: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id, is_published FROM courses WHERE id = :id", {"id": course_id})
    if not r:
        raise HTTPException(404, "Course not found")
    new_state = not bool(r["is_published"])
    await _exec("UPDATE courses SET is_published=:pub WHERE id=:id",
                {"pub": new_state, "id": course_id})
    return {"is_published": new_state, "message": "Published" if new_state else "Unpublished"}

@router.post("/lessons", status_code=201)
async def cms_create_lesson(data: LessonIn, _=Depends(get_admin_user)):
    now = datetime.utcnow()
    lid = await _exec(
        "INSERT INTO lessons (course_id, title, content, video_url, duration_minutes, order_index, created_at) "
        "VALUES (:cid,:title,:content,:video,:dur,:ord,:now)",
        {"cid": data.course_id, "title": data.title, "content": data.content or "",
         "video": data.video_url or "", "dur": data.duration_minutes or 0,
         "ord": data.order_index or 0, "now": now}
    )
    return {"id": lid, "message": "Lesson created"}

@router.put("/lessons/{lesson_id}")
async def cms_update_lesson(lesson_id: int, data: LessonIn, _=Depends(get_admin_user)):
    await _exec(
        "UPDATE lessons SET title=:title, content=:content, video_url=:video, "
        "duration_minutes=:dur, order_index=:ord WHERE id=:id",
        {"title": data.title, "content": data.content or "", "video": data.video_url or "",
         "dur": data.duration_minutes or 0, "ord": data.order_index or 0, "id": lesson_id}
    )
    return {"message": "Lesson updated"}

@router.delete("/lessons/{lesson_id}")
async def cms_delete_lesson(lesson_id: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM lessons WHERE id = :id", {"id": lesson_id})
    return {"message": "Lesson deleted"}


# ══════════════════════════════════════════════════════════════════════════════
# SIGNALS
# ══════════════════════════════════════════════════════════════════════════════

class SignalIn(BaseModel):
    symbol: str
    direction: str                      # BUY | SELL
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: Optional[str] = "1H"
    analysis: Optional[str] = ""
    ai_confidence: Optional[float] = None
    status: Optional[str] = "active"   # active | closed | cancelled

@router.get("/signals")
async def cms_list_signals(_=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT id, symbol, direction, entry_price, stop_loss, take_profit, "
        "timeframe, analysis, ai_confidence, status, outcome, created_at "
        "FROM signals ORDER BY created_at DESC LIMIT 200"
    )
    for r in rows:
        r["created_at"] = _fmt(r.get("created_at"))
    return rows

@router.post("/signals", status_code=201)
async def cms_create_signal(data: SignalIn, _=Depends(get_admin_user)):
    now = datetime.utcnow()
    sid = await _exec(
        "INSERT INTO signals (symbol, direction, entry_price, stop_loss, take_profit, "
        "timeframe, analysis, ai_confidence, status, created_at) "
        "VALUES (:sym,:dir,:entry,:sl,:tp,:tf,:analysis,:conf,:status,:now)",
        {"sym": data.symbol.upper(), "dir": data.direction.upper(),
         "entry": data.entry_price, "sl": data.stop_loss, "tp": data.take_profit,
         "tf": data.timeframe or "1H", "analysis": data.analysis or "",
         "conf": data.ai_confidence, "status": data.status or "active", "now": now}
    )
    return {"id": sid, "message": "Signal created"}

@router.put("/signals/{signal_id}")
async def cms_update_signal(signal_id: int, data: SignalIn, _=Depends(get_admin_user)):
    existing = await _row("SELECT id FROM signals WHERE id = :id", {"id": signal_id})
    if not existing:
        raise HTTPException(404, "Signal not found")
    await _exec(
        "UPDATE signals SET symbol=:sym, direction=:dir, entry_price=:entry, "
        "stop_loss=:sl, take_profit=:tp, timeframe=:tf, analysis=:analysis, "
        "ai_confidence=:conf, status=:status WHERE id=:id",
        {"sym": data.symbol.upper(), "dir": data.direction.upper(),
         "entry": data.entry_price, "sl": data.stop_loss, "tp": data.take_profit,
         "tf": data.timeframe or "1H", "analysis": data.analysis or "",
         "conf": data.ai_confidence, "status": data.status or "active", "id": signal_id}
    )
    return {"message": "Signal updated"}

@router.delete("/signals/{signal_id}")
async def cms_delete_signal(signal_id: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM signals WHERE id = :id", {"id": signal_id})
    return {"message": "Signal deleted"}

@router.post("/signals/{signal_id}/close")
async def cms_close_signal(signal_id: int, outcome: Optional[str] = "closed",
                           _=Depends(get_admin_user)):
    await _exec("UPDATE signals SET status='closed', outcome=:outcome WHERE id=:id",
                {"outcome": outcome, "id": signal_id})
    return {"message": f"Signal closed ({outcome})"}


# ══════════════════════════════════════════════════════════════════════════════
# WEBINARS
# ══════════════════════════════════════════════════════════════════════════════

class WebinarIn(BaseModel):
    title: str
    description: Optional[str] = ""
    presenter: Optional[str] = ""
    scheduled_at: str                   # ISO datetime string
    duration_minutes: Optional[int] = 60
    meeting_link: Optional[str] = ""
    max_attendees: Optional[int] = 100
    is_published: bool = False

@router.get("/webinars")
async def cms_list_webinars(_=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT id, title, description, presenter, scheduled_at, duration_minutes, "
        "meeting_link, max_attendees, is_published, created_at "
        "FROM webinars ORDER BY scheduled_at DESC"
    )
    for r in rows:
        r["scheduled_at"] = _fmt(r.get("scheduled_at"))
        r["created_at"]   = _fmt(r.get("created_at"))
    return rows

@router.post("/webinars", status_code=201)
async def cms_create_webinar(data: WebinarIn, _=Depends(get_admin_user)):
    try:
        sched = datetime.fromisoformat(data.scheduled_at.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, "Invalid scheduled_at datetime format")
    now = datetime.utcnow()
    wid = await _exec(
        "INSERT INTO webinars (title, description, presenter, scheduled_at, "
        "duration_minutes, meeting_link, max_attendees, is_published, created_at) "
        "VALUES (:title,:desc,:presenter,:sched,:dur,:link,:max,:pub,:now)",
        {"title": data.title, "desc": data.description or "",
         "presenter": data.presenter or "", "sched": sched,
         "dur": data.duration_minutes or 60, "link": data.meeting_link or "",
         "max": data.max_attendees or 100, "pub": data.is_published, "now": now}
    )
    return {"id": wid, "message": "Webinar created"}

@router.put("/webinars/{webinar_id}")
async def cms_update_webinar(webinar_id: int, data: WebinarIn, _=Depends(get_admin_user)):
    existing = await _row("SELECT id FROM webinars WHERE id = :id", {"id": webinar_id})
    if not existing:
        raise HTTPException(404, "Webinar not found")
    try:
        sched = datetime.fromisoformat(data.scheduled_at.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, "Invalid scheduled_at datetime format")
    await _exec(
        "UPDATE webinars SET title=:title, description=:desc, presenter=:presenter, "
        "scheduled_at=:sched, duration_minutes=:dur, meeting_link=:link, "
        "max_attendees=:max, is_published=:pub WHERE id=:id",
        {"title": data.title, "desc": data.description or "",
         "presenter": data.presenter or "", "sched": sched,
         "dur": data.duration_minutes or 60, "link": data.meeting_link or "",
         "max": data.max_attendees or 100, "pub": data.is_published, "id": webinar_id}
    )
    return {"message": "Webinar updated"}

@router.delete("/webinars/{webinar_id}")
async def cms_delete_webinar(webinar_id: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM webinars WHERE id = :id", {"id": webinar_id})
    return {"message": "Webinar deleted"}

@router.post("/webinars/{webinar_id}/toggle-publish")
async def cms_toggle_webinar(webinar_id: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id, is_published FROM webinars WHERE id = :id", {"id": webinar_id})
    if not r:
        raise HTTPException(404, "Webinar not found")
    new_state = not bool(r["is_published"])
    await _exec("UPDATE webinars SET is_published=:pub WHERE id=:id",
                {"pub": new_state, "id": webinar_id})
    return {"is_published": new_state, "message": "Published" if new_state else "Unpublished"}


# ══════════════════════════════════════════════════════════════════════════════
# SITE SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

# Ensure the table exists at startup (called from lifespan in main.py if desired).
_CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS site_settings (
    key         VARCHAR(120) PRIMARY KEY,
    value       TEXT         NOT NULL DEFAULT '',
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
)
"""

_DEFAULT_SETTINGS = {
    "site_name":          "Pipways",
    "site_tagline":       "Professional Trading Platform",
    "contact_email":      "support@pipways.com",
    "support_email":      "support@pipways.com",
    "twitter_url":        "",
    "instagram_url":      "",
    "telegram_url":       "",
    "youtube_url":        "",
    "discord_url":        "",
    "logo_url":           "",
    "favicon_url":        "",
    "maintenance_mode":   "false",
    "allow_registration": "true",
    "free_signals_limit": "3",
    "currency":           "USD",
    "timezone":           "UTC",
    "analytics_id":       "",
    "smtp_host":          "",
    "smtp_port":          "587",
    "smtp_user":          "",
    "footer_text":        "© 2025 Pipways. All rights reserved.",
}

async def _ensure_settings_table():
    """Create site_settings table and seed defaults if missing."""
    try:
        await database.execute(_CREATE_SETTINGS_TABLE)
        for key, default_value in _DEFAULT_SETTINGS.items():
            await database.execute(
                "INSERT INTO site_settings (key, value, updated_at) "
                "VALUES (:key, :val, NOW()) "
                "ON CONFLICT (key) DO NOTHING",
                {"key": key, "val": default_value}
            )
    except Exception as e:
        print(f"[CMS] settings table init: {e}", flush=True)

@router.get("/settings")
async def cms_get_settings(_=Depends(get_admin_user)):
    await _ensure_settings_table()
    rows = await _rows("SELECT key, value, updated_at FROM site_settings ORDER BY key")
    return {r["key"]: r["value"] for r in rows}

@router.put("/settings")
async def cms_update_settings(updates: dict, _=Depends(get_admin_user)):
    """Accept a flat {key: value} dict and upsert each pair."""
    await _ensure_settings_table()
    now = datetime.utcnow()
    for key, value in updates.items():
        if not isinstance(key, str) or len(key) > 120:
            continue
        await _exec(
            "INSERT INTO site_settings (key, value, updated_at) VALUES (:key,:val,:now) "
            "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=EXCLUDED.updated_at",
            {"key": key, "val": str(value), "now": now}
        )
    return {"message": f"Saved {len(updates)} setting(s)"}
