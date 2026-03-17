"""
CMS API v2 — Full Content Management System
New in v2:
  • Media upload / library (stored in static/uploads/, served at /static/uploads/)
  • User management  (role promotion, subscription tier, ban/unban)
  • AI SEO scoring   (readability + keyword + structure analysis via OpenRouter)
  • Course Modules   (course → modules → lessons hierarchy)
  • Quizzes          (module → quiz → questions → options)
  • Coupons          (discount codes for courses)
  • Announcements    (site-wide banners)

All endpoints require admin authentication via get_admin_user().
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import json, os, uuid, mimetypes, httpx

from .admin import get_admin_user
from .database import database

router = APIRouter()

# ── Upload directory ────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR  = os.path.join(BASE_DIR, "frontend", "static", "uploads")
UPLOAD_URL  = "/static/uploads"
MAX_UPLOAD  = 20 * 1024 * 1024   # 20 MB

ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml",
    "video/mp4", "video/webm",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── OpenRouter key (reused from chart_analysis) ─────────────────────────────
_OR_KEY   = os.getenv("OPENROUTER_API_KEY", "")
_OR_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

# ── Helpers ─────────────────────────────────────────────────────────────────

def _fmt(v):
    if isinstance(v, datetime): return v.isoformat()
    return str(v) if v is not None else ""

async def _row(q, v=None):
    try:
        r = await database.fetch_one(q, v or {})
        return dict(r) if r else None
    except Exception as e:
        print(f"[CMS] row: {e}", flush=True); return None

async def _rows(q, v=None):
    try:
        rs = await database.fetch_all(q, v or {})
        return [dict(r) for r in rs] if rs else []
    except Exception as e:
        print(f"[CMS] _rows ERROR: {e} | query: {str(q)[:120]}", flush=True)
        return []

async def _exec(q, v=None):
    try:
        return await database.execute(q, v or {})
    except Exception as e:
        print(f"[CMS] exec: {e}", flush=True)
        raise HTTPException(500, f"Database error: {str(e)}")

def _tags_str(t):
    """
    Return tags in the correct format for asyncpg.
    The DB column may be TEXT (store as JSON string) or TEXT[] (store as list).
    We always return a JSON string for TEXT columns — asyncpg handles TEXT fine.
    For TEXT[] columns asyncpg needs a Python list.
    We detect by trying JSON string first; if that causes 'sized iterable' errors
    the fallback in cms_create_post/update handles it.
    """
    if isinstance(t, list):
        return json.dumps(t)          # TEXT column: store as JSON string
    if not t:
        return '[]'
    try:
        parsed = json.loads(t)
        return json.dumps(parsed) if isinstance(parsed, list) else json.dumps([])
    except Exception:
        items = [x.strip() for x in str(t).split(",") if x.strip()]
        return json.dumps(items)


def _tags_list_val(t):
    """Return tags as a Python list (for TEXT[] columns)."""
    if isinstance(t, list):
        return t
    if not t:
        return []
    try:
        parsed = json.loads(t)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return [x.strip() for x in str(t).split(",") if x.strip()]

def _tags_list(r):
    if not r: return []
    if isinstance(r, list): return r
    try: return json.loads(r)
    except: return [x.strip() for x in str(r).split(",") if x.strip()]


# ══════════════════════════════════════════════════════════════════════════════
# MEDIA LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/media/upload", status_code=201)
async def cms_upload_media(
    file: UploadFile = File(...),
    folder: str = Form("general"),
    _=Depends(get_admin_user)
):
    """Upload a file; returns the public URL."""
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, f"File type '{file.content_type}' not allowed")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD:
        raise HTTPException(400, "File too large (max 20 MB)")

    ext       = mimetypes.guess_extension(file.content_type) or os.path.splitext(file.filename or "")[1] or ".bin"
    ext       = ext.lstrip(".")
    safe_name = f"{folder}/{uuid.uuid4().hex}.{ext}"
    dest_dir  = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(UPLOAD_DIR, safe_name.replace("/", os.sep))

    with open(dest_path, "wb") as f:
        f.write(contents)

    # Persist to media_library table if it exists
    try:
        await _exec(
            "INSERT INTO media_library (filename, original_name, url, mime_type, size_bytes, folder, created_at) "
            "VALUES (:fn,:orig,:url,:mime,:size,:folder,:now)",
            {"fn": safe_name, "orig": file.filename, "url": f"{UPLOAD_URL}/{safe_name}",
             "mime": file.content_type, "size": len(contents),
             "folder": folder, "now": datetime.utcnow()}
        )
    except Exception:
        pass  # table may not exist yet, URL is still valid

    return {
        "url":           f"{UPLOAD_URL}/{safe_name}",
        "filename":      safe_name,
        "original_name": file.filename,
        "mime_type":     file.content_type,
        "size_bytes":    len(contents),
    }

@router.get("/media")
async def cms_list_media(folder: Optional[str] = None, _=Depends(get_admin_user)):
    """List uploaded files from DB if available, else scan disk."""
    try:
        q = "SELECT * FROM media_library"
        v = {}
        if folder:
            q += " WHERE folder = :folder"
            v["folder"] = folder
        q += " ORDER BY created_at DESC LIMIT 200"
        rows = await _rows(q, v)
        if rows:
            for r in rows:
                r["created_at"] = _fmt(r.get("created_at"))
            return rows
    except Exception:
        pass

    # Fallback: scan upload directory
    results = []
    for root, _, files in os.walk(UPLOAD_DIR):
        for fn in files:
            full = os.path.join(root, fn)
            rel  = os.path.relpath(full, UPLOAD_DIR).replace(os.sep, "/")
            results.append({
                "url":      f"{UPLOAD_URL}/{rel}",
                "filename": rel,
                "original_name": fn,
                "size_bytes": os.path.getsize(full),
            })
    return results[-200:]

@router.delete("/media")
async def cms_delete_media(filename: str, _=Depends(get_admin_user)):
    """Delete a media file by its relative filename."""
    safe = filename.replace("..", "").lstrip("/")
    path = os.path.join(UPLOAD_DIR, safe.replace("/", os.sep))
    if os.path.exists(path):
        os.remove(path)
    try:
        await _exec("DELETE FROM media_library WHERE filename = :fn", {"fn": safe})
    except Exception:
        pass
    return {"message": "File deleted"}


# ══════════════════════════════════════════════════════════════════════════════
# BLOG  (unchanged endpoints + new SEO scoring)
# ══════════════════════════════════════════════════════════════════════════════

class BlogPostIn(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = ""
    content: str
    category: Optional[str] = "General"
    tags: Optional[Any] = []
    featured_image: Optional[str] = ""
    seo_title: Optional[str] = ""
    seo_description: Optional[str] = ""
    focus_keyword: Optional[str] = ""
    is_published: bool = False

@router.get("/blog")
async def cms_list_posts(_=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT id, title, slug, excerpt, category, tags, featured_image, "
        "is_published, views, seo_title, seo_description, focus_keyword, "
        "created_at, updated_at FROM blog_posts ORDER BY created_at DESC"
    )
    for r in rows:
        r["tags"]       = _tags_list(r.get("tags"))
        r["created_at"] = _fmt(r.get("created_at"))
        r["updated_at"] = _fmt(r.get("updated_at"))
    return rows

@router.get("/blog/{post_id}")
async def cms_get_post(post_id: int, _=Depends(get_admin_user)):
    r = await _row("SELECT * FROM blog_posts WHERE id = :id", {"id": post_id})
    if not r: raise HTTPException(404, "Post not found")
    r["tags"] = _tags_list(r.get("tags"))
    return r

@router.post("/blog", status_code=201)
async def cms_create_post(data: BlogPostIn, _=Depends(get_admin_user)):
    if await _row("SELECT id FROM blog_posts WHERE slug=:s", {"s": data.slug}):
        raise HTTPException(400, f"Slug '{data.slug}' already exists")
    now = datetime.utcnow()

    # Try with tags as JSON string (TEXT column)
    try:
        pid = await _exec(
            "INSERT INTO blog_posts (title,slug,excerpt,content,category,tags,featured_image,"
            "seo_title,seo_description,focus_keyword,is_published,status,views,created_at,updated_at) "
            "VALUES (:title,:slug,:excerpt,:content,:cat,:tags,:img,:stitle,:sdesc,:kw,:pub,:status,0,:now,:now)"
            " RETURNING id",
            {"title":data.title,"slug":data.slug,"excerpt":data.excerpt or "","content":data.content,
             "cat":data.category or "General","tags":_tags_str(data.tags),"img":data.featured_image or "",
             "stitle":data.seo_title or "","sdesc":data.seo_description or "","kw":data.focus_keyword or "",
             "pub":data.is_published,"status":"published" if data.is_published else "draft","now":now}
        )
    except Exception as e:
        if "iterable" in str(e).lower() or "array" in str(e).lower() or "sized" in str(e).lower():
            # tags column is TEXT[] — pass as Python list
            pid = await _exec(
                "INSERT INTO blog_posts (title,slug,excerpt,content,category,tags,featured_image,"
                "seo_title,seo_description,focus_keyword,is_published,status,views,created_at,updated_at) "
                "VALUES (:title,:slug,:excerpt,:content,:cat,:tags,:img,:stitle,:sdesc,:kw,:pub,:status,0,:now,:now)",
                {"title":data.title,"slug":data.slug,"excerpt":data.excerpt or "","content":data.content,
                 "cat":data.category or "General","tags":_tags_list_val(data.tags),"img":data.featured_image or "",
                 "stitle":data.seo_title or "","sdesc":data.seo_description or "","kw":data.focus_keyword or "",
                 "pub":data.is_published,"status":"published" if data.is_published else "draft","now":now}
            )
        else:
            raise
    return {"id": pid, "message": "Post created"}

@router.put("/blog/{post_id}")
async def cms_update_post(post_id: int, data: BlogPostIn, _=Depends(get_admin_user)):
    if not await _row("SELECT id FROM blog_posts WHERE id=:id", {"id": post_id}):
        raise HTTPException(404, "Post not found")
    sql = ("UPDATE blog_posts SET title=:title,slug=:slug,excerpt=:excerpt,content=:content,"
           "category=:cat,tags=:tags,featured_image=:img,seo_title=:stitle,seo_description=:sdesc,"
           "focus_keyword=:kw,is_published=:pub,status=:status,updated_at=:now WHERE id=:id")
    base = {"title":data.title,"slug":data.slug,"excerpt":data.excerpt or "","content":data.content,
            "cat":data.category or "General","img":data.featured_image or "",
            "stitle":data.seo_title or "","sdesc":data.seo_description or "","kw":data.focus_keyword or "",
            "pub":data.is_published,"status":"published" if data.is_published else "draft",
            "now":datetime.utcnow(),"id":post_id}
    try:
        await _exec(sql, {**base, "tags": _tags_str(data.tags)})
    except Exception as e:
        if "iterable" in str(e).lower() or "array" in str(e).lower() or "sized" in str(e).lower():
            await _exec(sql, {**base, "tags": _tags_list_val(data.tags)})
        else:
            raise
    return {"message": "Post updated"}

@router.delete("/blog/{post_id}")
async def cms_delete_post(post_id: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM blog_posts WHERE id=:id", {"id": post_id})
    return {"message": "Post deleted"}

@router.post("/blog/{post_id}/toggle-publish")
async def cms_toggle_post(post_id: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id,is_published FROM blog_posts WHERE id=:id", {"id": post_id})
    if not r: raise HTTPException(404, "Post not found")
    ns = not bool(r["is_published"])
    # Sync both is_published and legacy status column
    await _exec("UPDATE blog_posts SET is_published=:pub,status=:status,updated_at=:now WHERE id=:id",
                {"pub": ns, "status": "published" if ns else "draft",
                 "now": datetime.utcnow(), "id": post_id})
    return {"is_published": ns, "message": "Published" if ns else "Unpublished"}

class SEORequest(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = ""
    focus_keyword: Optional[str] = ""
    slug: Optional[str] = ""

@router.post("/blog/seo-score")
async def cms_seo_score(data: SEORequest, _=Depends(get_admin_user)):
    """
    AI-powered SEO analysis. Returns a 0-100 score + actionable suggestions.
    Falls back to rule-based scoring if OpenRouter is not configured.
    """
    title    = data.title or ""
    content  = data.content or ""
    excerpt  = data.excerpt or ""
    keyword  = (data.focus_keyword or "").lower().strip()
    slug     = data.slug or ""
    words    = [w for w in content.split() if w]
    word_count = len(words)

    # ── Rule-based scoring (always runs) ──────────────────────────────────
    checks = []
    score  = 0

    def chk(passed: bool, points: int, label: str, tip: str):
        nonlocal score
        if passed: score += points
        checks.append({"passed": passed, "label": label, "tip": tip, "points": points})

    t_len = len(title)
    chk(50 <= t_len <= 60,  10, f"Title length ({t_len} chars)",
        "Aim for 50-60 characters. Google truncates longer titles." if t_len > 60 else
        "Title is too short — expand to 50-60 characters for best CTR.")

    chk(word_count >= 300,   10, f"Word count ({word_count} words)",
        "Content is thin. Aim for at least 600 words for good rankings." if word_count < 300 else "")

    chk(word_count >= 600,    5, f"Long-form content ({word_count} words)",
        "Long-form posts (1000+) tend to rank higher.")

    chk(bool(excerpt) and 120 <= len(excerpt) <= 160,  8, "Meta description length",
        "Write an excerpt of 120-160 characters — shown in search results.")

    chk(bool(data.featured_image if hasattr(data,'featured_image') else True), 5, "Featured image",
        "Add a featured image with descriptive filename and alt text.")

    if keyword:
        kw_in_title   = keyword in title.lower()
        kw_in_content = content.lower().count(keyword)
        kw_in_slug    = keyword.replace(" ", "-") in slug.lower() or keyword in slug.lower()
        kw_in_excerpt = keyword in excerpt.lower()
        density = kw_in_content / max(word_count, 1) * 100

        chk(kw_in_title,   12, f"Keyword '{keyword}' in title",      "Add focus keyword to the title.")
        chk(kw_in_slug,     8, f"Keyword '{keyword}' in URL slug",    "Include keyword in the slug/URL.")
        chk(kw_in_excerpt,  6, f"Keyword '{keyword}' in excerpt",     "Include keyword in the meta description.")
        chk(kw_in_content >= 2,  6, f"Keyword appears in content ({kw_in_content}×)", "Use keyword naturally throughout the content.")
        chk(0.5 <= density <= 2.5, 4, f"Keyword density ({density:.1f}%)",
            "Aim for 0.5-2.5% density. Over-use is penalised (keyword stuffing).")
    else:
        checks.append({"passed": False, "label": "Focus keyword set", "tip": "Set a focus keyword to enable keyword analysis.", "points": 36})

    h2_count = content.lower().count("<h2") + content.count("## ")
    h3_count = content.lower().count("<h3") + content.count("### ")
    chk(h2_count >= 2,  8, f"Subheadings (H2: {h2_count}, H3: {h3_count})",
        "Use at least 2 H2 subheadings to structure content for readers and crawlers.")

    link_count = content.count("http") + content.count("](")
    chk(link_count >= 2,  5, f"Internal/external links ({link_count})",
        "Add at least 2 relevant links (internal or external) to increase credibility.")

    chk(bool(slug) and "-" in slug and len(slug) <= 75, 5, "URL slug quality",
        "Use hyphens, keep under 75 characters, include the focus keyword.")

    score = min(score, 100)

    # ── Optional AI enhancement via OpenRouter ────────────────────────────
    ai_suggestions: list[str] = []
    if _OR_KEY and word_count > 50:
        try:
            prompt = f"""You are an expert SEO consultant. Analyse this blog post and give 5 concise, actionable SEO improvement tips.

Title: {title}
Focus Keyword: {keyword or 'not set'}
Word Count: {word_count}
Current Score: {score}/100

Content (first 800 chars): {content[:800]}

Return ONLY a JSON array of 5 short tip strings, e.g.:
["tip1","tip2","tip3","tip4","tip5"]"""
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {_OR_KEY}",
                             "Content-Type": "application/json"},
                    json={"model": _OR_MODEL,
                          "messages": [{"role": "user", "content": prompt}],
                          "max_tokens": 400, "temperature": 0.3}
                )
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"]
                raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                tips = json.loads(raw)
                if isinstance(tips, list):
                    ai_suggestions = [str(t) for t in tips[:5]]
        except Exception as e:
            print(f"[CMS SEO] AI tip error: {e}", flush=True)

    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    return {
        "score": score,
        "grade": grade,
        "word_count": word_count,
        "checks": checks,
        "ai_suggestions": ai_suggestions,
        "ai_powered": bool(ai_suggestions),
    }


# ══════════════════════════════════════════════════════════════════════════════
# COURSES / LMS  — Modules → Lessons → Quizzes
# ══════════════════════════════════════════════════════════════════════════════

class CourseIn(BaseModel):
    title: str
    description: Optional[str] = ""
    level: Optional[str] = "Beginner"
    price: Optional[float] = 0.0
    thumbnail: Optional[str] = ""
    preview_video: Optional[str] = ""
    is_published: bool = False
    certificate_enabled: bool = False
    pass_percentage: Optional[int] = 70

class ModuleIn(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = ""
    order_index: Optional[int] = 0

class LessonIn(BaseModel):
    module_id: int
    course_id: int
    title: str
    content: Optional[str] = ""
    video_url: Optional[str] = ""
    attachment_url: Optional[str] = ""
    duration_minutes: Optional[int] = 0
    order_index: Optional[int] = 0
    is_free_preview: bool = False

class QuizIn(BaseModel):
    module_id: int
    title: str
    pass_percentage: Optional[int] = 70
    max_attempts: Optional[int] = 3

class QuestionIn(BaseModel):
    quiz_id: int
    question: str
    option_a: str
    option_b: str
    option_c: Optional[str] = ""
    option_d: Optional[str] = ""
    correct_option: str       # "a" | "b" | "c" | "d"
    explanation: Optional[str] = ""
    order_index: Optional[int] = 0

# ── Courses ──────────────────────────────────────────────────────────────────

@router.get("/courses")
async def cms_list_courses(_=Depends(get_admin_user)):
    rows = []
    try:
        rows = await _rows(
            "SELECT c.id,c.title,c.description,c.level,c.price,c.thumbnail,c.preview_video,"
            "c.is_published,c.certificate_enabled,c.pass_percentage,c.created_at,"
            "COUNT(DISTINCT m.id) AS module_count,"
            "COUNT(DISTINCT l.id) AS lesson_count "
            "FROM courses c "
            "LEFT JOIN course_modules m ON m.course_id=c.id "
            "LEFT JOIN lessons l ON l.course_id=c.id "
            "GROUP BY c.id ORDER BY c.created_at DESC"
        )
        print(f"[CMS] listCourses (full join): {len(rows)} rows", flush=True)
    except Exception as e1:
        print(f"[CMS] listCourses full join failed ({e1}), using simple query", flush=True)
        try:
            rows = await _rows(
                "SELECT id,title,description,level,is_published,created_at "
                "FROM courses ORDER BY created_at DESC"
            )
            for r in rows:
                r.setdefault("price", 0)
                r.setdefault("thumbnail", "")
                r.setdefault("preview_video", "")
                r.setdefault("certificate_enabled", False)
                r.setdefault("pass_percentage", 70)
            print(f"[CMS] listCourses (simple): {len(rows)} rows", flush=True)
        except Exception as e2:
            print(f"[CMS] listCourses simple query also failed: {e2}", flush=True)
            return []
    for r in rows:
        r["created_at"]   = _fmt(r.get("created_at"))
        r["module_count"] = r.get("module_count") or 0
        r["lesson_count"] = r.get("lesson_count") or 0
    return rows

@router.post("/courses", status_code=201)
async def cms_create_course(data: CourseIn, _=Depends(get_admin_user)):
    print(f"[CMS] Creating course: title={data.title!r} published={data.is_published}", flush=True)
    cid = None
    try:
        cid = await _exec(
            "INSERT INTO courses (title,description,level,price,thumbnail,preview_video,"
            "is_published,is_active,certificate_enabled,pass_percentage,created_at) "
            "VALUES (:title,:desc,:level,:price,:thumb,:preview,:pub,:active,:cert,:pass,:now)"
            " RETURNING id",
            {"title":data.title,"desc":data.description or "","level":data.level or "Beginner",
             "price":data.price or 0,"thumb":data.thumbnail or "","preview":data.preview_video or "",
             "pub":data.is_published,"active":data.is_published,
             "cert":data.certificate_enabled,"pass":data.pass_percentage or 70,
             "now":datetime.utcnow()}
        )
        print(f"[CMS] Course created with id={cid} (full insert)", flush=True)
    except Exception as e1:
        print(f"[CMS] Full insert failed ({e1}), trying fallback insert", flush=True)
        try:
            cid = await _exec(
                "INSERT INTO courses (title,description,level,price,thumbnail,preview_video,"
                "is_published,certificate_enabled,pass_percentage,created_at) "
                "VALUES (:title,:desc,:level,:price,:thumb,:preview,:pub,:cert,:pass,:now)"
                " RETURNING id",
                {"title":data.title,"desc":data.description or "","level":data.level or "Beginner",
                 "price":data.price or 0,"thumb":data.thumbnail or "","preview":data.preview_video or "",
                 "pub":data.is_published,
                 "cert":data.certificate_enabled,"pass":data.pass_percentage or 70,
                 "now":datetime.utcnow()}
            )
            print(f"[CMS] Course created with id={cid} (fallback insert)", flush=True)
        except Exception as e2:
            print(f"[CMS] Fallback insert also failed: {e2}", flush=True)
            raise HTTPException(500, f"Could not create course: {e2}")
    if not cid:
        raise HTTPException(500, "Course insert returned no ID")
    return {"id": cid, "message": "Course created"}

@router.put("/courses/{cid}")
async def cms_update_course(cid: int, data: CourseIn, _=Depends(get_admin_user)):
    if not await _row("SELECT id FROM courses WHERE id=:id", {"id": cid}):
        raise HTTPException(404, "Course not found")
    try:
        await _exec(
            "UPDATE courses SET title=:title,description=:desc,level=:level,price=:price,"
            "thumbnail=:thumb,preview_video=:preview,is_published=:pub,is_active=:active,"
            "certificate_enabled=:cert,pass_percentage=:pass WHERE id=:id",
            {"title":data.title,"desc":data.description or "","level":data.level or "Beginner",
             "price":data.price or 0,"thumb":data.thumbnail or "","preview":data.preview_video or "",
             "pub":data.is_published,"active":data.is_published,
             "cert":data.certificate_enabled,"pass":data.pass_percentage or 70,"id":cid}
        )
    except Exception:
        # Fallback: is_active column not yet added
        await _exec(
            "UPDATE courses SET title=:title,description=:desc,level=:level,price=:price,"
            "thumbnail=:thumb,preview_video=:preview,is_published=:pub,"
            "certificate_enabled=:cert,pass_percentage=:pass WHERE id=:id",
            {"title":data.title,"desc":data.description or "","level":data.level or "Beginner",
             "price":data.price or 0,"thumb":data.thumbnail or "","preview":data.preview_video or "",
             "pub":data.is_published,
             "cert":data.certificate_enabled,"pass":data.pass_percentage or 70,"id":cid}
        )
    return {"message": "Course updated"}

@router.delete("/courses/{cid}")
async def cms_delete_course(cid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM quiz_questions WHERE quiz_id IN (SELECT id FROM quizzes WHERE module_id IN (SELECT id FROM course_modules WHERE course_id=:id))", {"id": cid})
    await _exec("DELETE FROM quizzes WHERE module_id IN (SELECT id FROM course_modules WHERE course_id=:id)", {"id": cid})
    await _exec("DELETE FROM lessons WHERE course_id=:id", {"id": cid})
    await _exec("DELETE FROM course_modules WHERE course_id=:id", {"id": cid})
    await _exec("DELETE FROM courses WHERE id=:id", {"id": cid})
    return {"message": "Course and all content deleted"}

@router.post("/courses/{cid}/toggle-publish")
async def cms_toggle_course(cid: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id,is_published FROM courses WHERE id=:id", {"id": cid})
    if not r: raise HTTPException(404, "Course not found")
    ns = not bool(r["is_published"])
    # Sync both is_published and is_active so public /courses/list sees it
    try:
        await _exec("UPDATE courses SET is_published=:pub,is_active=:pub WHERE id=:id",
                    {"pub": ns, "id": cid})
    except Exception:
        await _exec("UPDATE courses SET is_published=:pub WHERE id=:id",
                    {"pub": ns, "id": cid})
    return {"is_published": ns, "message": "Published" if ns else "Unpublished"}

# ── Modules ──────────────────────────────────────────────────────────────────

@router.get("/courses/{cid}/modules")
async def cms_list_modules(cid: int, _=Depends(get_admin_user)):
    try:
        mods = await _rows(
            "SELECT m.id,m.title,m.description,m.order_index,"
            "COUNT(l.id) AS lesson_count,"
            "(SELECT COUNT(*) FROM quizzes q WHERE q.module_id=m.id) AS quiz_count "
            "FROM course_modules m LEFT JOIN lessons l ON l.module_id=m.id "
            "WHERE m.course_id=:cid GROUP BY m.id ORDER BY m.order_index,m.id",
            {"cid": cid}
        )
    except Exception:
        # Fallback: no JOIN if new tables not yet created
        mods = await _rows(
            "SELECT id,title,description,order_index FROM course_modules "
            "WHERE course_id=:cid ORDER BY order_index,id",
            {"cid": cid}
        )
    for m in mods:
        m["lesson_count"] = m.get("lesson_count") or 0
        m["quiz_count"]   = m.get("quiz_count")   or 0
    return mods

@router.post("/modules", status_code=201)
async def cms_create_module(data: ModuleIn, _=Depends(get_admin_user)):
    mid = await _exec(
        "INSERT INTO course_modules (course_id,title,description,order_index) VALUES (:cid,:title,:desc,:ord) RETURNING id",
        {"cid":data.course_id,"title":data.title,"desc":data.description or "","ord":data.order_index or 0}
    )
    return {"id": mid, "message": "Module created"}

@router.put("/modules/{mid}")
async def cms_update_module(mid: int, data: ModuleIn, _=Depends(get_admin_user)):
    await _exec(
        "UPDATE course_modules SET title=:title,description=:desc,order_index=:ord WHERE id=:id",
        {"title":data.title,"desc":data.description or "","ord":data.order_index or 0,"id":mid}
    )
    return {"message": "Module updated"}

@router.delete("/modules/{mid}")
async def cms_delete_module(mid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM quiz_questions WHERE quiz_id IN (SELECT id FROM quizzes WHERE module_id=:id)", {"id": mid})
    await _exec("DELETE FROM quizzes WHERE module_id=:id", {"id": mid})
    await _exec("DELETE FROM lessons WHERE module_id=:id", {"id": mid})
    await _exec("DELETE FROM course_modules WHERE id=:id", {"id": mid})
    return {"message": "Module and its lessons/quiz deleted"}

# ── Lessons ──────────────────────────────────────────────────────────────────

@router.get("/modules/{mid}/lessons")
async def cms_list_lessons(mid: int, _=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT * FROM lessons WHERE module_id=:mid ORDER BY order_index,id",
        {"mid": mid}
    )
    for r in rows:
        r["created_at"] = _fmt(r.get("created_at"))
    return rows

@router.post("/lessons", status_code=201)
async def cms_create_lesson(data: LessonIn, _=Depends(get_admin_user)):
    lid = await _exec(
        "INSERT INTO lessons (module_id,course_id,title,content,video_url,attachment_url,"
        "duration_minutes,order_index,is_free_preview,created_at) "
        "VALUES (:mid,:cid,:title,:content,:video,:attach,:dur,:ord,:preview,:now) RETURNING id",
        {"mid":data.module_id,"cid":data.course_id,"title":data.title,"content":data.content or "",
         "video":data.video_url or "","attach":data.attachment_url or "",
         "dur":data.duration_minutes or 0,"ord":data.order_index or 0,
         "preview":data.is_free_preview,"now":datetime.utcnow()}
    )
    return {"id": lid, "message": "Lesson created"}

@router.put("/lessons/{lid}")
async def cms_update_lesson(lid: int, data: LessonIn, _=Depends(get_admin_user)):
    await _exec(
        "UPDATE lessons SET title=:title,content=:content,video_url=:video,"
        "attachment_url=:attach,duration_minutes=:dur,order_index=:ord,"
        "is_free_preview=:preview WHERE id=:id",
        {"title":data.title,"content":data.content or "","video":data.video_url or "",
         "attach":data.attachment_url or "","dur":data.duration_minutes or 0,
         "ord":data.order_index or 0,"preview":data.is_free_preview,"id":lid}
    )
    return {"message": "Lesson updated"}

@router.delete("/lessons/{lid}")
async def cms_delete_lesson(lid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM lessons WHERE id=:id", {"id": lid})
    return {"message": "Lesson deleted"}

# ── Quizzes ──────────────────────────────────────────────────────────────────

@router.get("/modules/{mid}/quiz")
async def cms_get_quiz(mid: int, _=Depends(get_admin_user)):
    quiz = await _row("SELECT * FROM quizzes WHERE module_id=:mid", {"mid": mid})
    if not quiz:
        return None
    questions = await _rows(
        "SELECT * FROM quiz_questions WHERE quiz_id=:qid ORDER BY order_index,id",
        {"qid": quiz["id"]}
    )
    quiz["questions"] = questions
    return quiz

@router.post("/quizzes", status_code=201)
async def cms_create_quiz(data: QuizIn, _=Depends(get_admin_user)):
    qid = await _exec(
        "INSERT INTO quizzes (module_id,title,pass_percentage,max_attempts,created_at) "
        "VALUES (:mid,:title,:pass,:attempts,:now) RETURNING id",
        {"mid":data.module_id,"title":data.title,"pass":data.pass_percentage or 70,
         "attempts":data.max_attempts or 3,"now":datetime.utcnow()}
    )
    return {"id": qid, "message": "Quiz created"}

@router.put("/quizzes/{qid}")
async def cms_update_quiz(qid: int, data: QuizIn, _=Depends(get_admin_user)):
    await _exec(
        "UPDATE quizzes SET title=:title,pass_percentage=:pass,max_attempts=:attempts WHERE id=:id",
        {"title":data.title,"pass":data.pass_percentage or 70,"attempts":data.max_attempts or 3,"id":qid}
    )
    return {"message": "Quiz updated"}

@router.delete("/quizzes/{qid}")
async def cms_delete_quiz(qid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM quiz_questions WHERE quiz_id=:id", {"id": qid})
    await _exec("DELETE FROM quizzes WHERE id=:id", {"id": qid})
    return {"message": "Quiz and questions deleted"}

@router.post("/quiz-questions", status_code=201)
async def cms_create_question(data: QuestionIn, _=Depends(get_admin_user)):
    qid = await _exec(
        "INSERT INTO quiz_questions (quiz_id,question,option_a,option_b,option_c,option_d,"
        "correct_option,explanation,order_index) "
        "VALUES (:qid,:q,:a,:b,:c,:d,:correct,:expl,:ord) RETURNING id",
        {"qid":data.quiz_id,"q":data.question,"a":data.option_a,"b":data.option_b,
         "c":data.option_c or "","d":data.option_d or "","correct":data.correct_option.lower(),
         "expl":data.explanation or "","ord":data.order_index or 0}
    )
    return {"id": qid, "message": "Question added"}

@router.put("/quiz-questions/{qid}")
async def cms_update_question(qid: int, data: QuestionIn, _=Depends(get_admin_user)):
    await _exec(
        "UPDATE quiz_questions SET question=:q,option_a=:a,option_b=:b,option_c=:c,"
        "option_d=:d,correct_option=:correct,explanation=:expl,order_index=:ord WHERE id=:id",
        {"q":data.question,"a":data.option_a,"b":data.option_b,"c":data.option_c or "",
         "d":data.option_d or "","correct":data.correct_option.lower(),
         "expl":data.explanation or "","ord":data.order_index or 0,"id":qid}
    )
    return {"message": "Question updated"}

@router.delete("/quiz-questions/{qid}")
async def cms_delete_question(qid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM quiz_questions WHERE id=:id", {"id": qid})
    return {"message": "Question deleted"}


# ══════════════════════════════════════════════════════════════════════════════
# SIGNALS  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

class SignalIn(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: Optional[str] = "1H"
    analysis: Optional[str] = ""
    ai_confidence: Optional[float] = None
    status: Optional[str] = "active"

@router.get("/signals")
async def cms_list_signals(_=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT id,symbol,direction,entry_price,stop_loss,take_profit,"
        "timeframe,analysis,ai_confidence,status,is_published,outcome,created_at "
        "FROM signals ORDER BY created_at DESC LIMIT 200"
    )
    for r in rows: r["created_at"] = _fmt(r.get("created_at"))
    return rows

@router.post("/signals", status_code=201)
async def cms_create_signal(data: SignalIn, _=Depends(get_admin_user)):
    sid = await _exec(
        "INSERT INTO signals (symbol,direction,entry_price,stop_loss,take_profit,"
        "timeframe,analysis,ai_confidence,status,created_at) "
        "VALUES (:sym,:dir,:entry,:sl,:tp,:tf,:anal,:conf,:status,:now) RETURNING id",
        {"sym":data.symbol.upper(),"dir":data.direction.upper(),
         "entry":data.entry_price,"sl":data.stop_loss,"tp":data.take_profit,
         "tf":data.timeframe or "1H","anal":data.analysis or "",
         "conf":data.ai_confidence,"status":data.status or "active","now":datetime.utcnow()}
    )
    # Backfill pair column if it exists (older schema had pair NOT NULL)
    try:
        await _exec("UPDATE signals SET pair=:p WHERE id=:id", {"p": data.symbol.upper(), "id": sid})
    except Exception:
        pass
    return {"id": sid, "message": "Signal created"}

@router.put("/signals/{sid}")
async def cms_update_signal(sid: int, data: SignalIn, _=Depends(get_admin_user)):
    if not await _row("SELECT id FROM signals WHERE id=:id", {"id": sid}):
        raise HTTPException(404, "Signal not found")
    await _exec(
        "UPDATE signals SET symbol=:sym,direction=:dir,entry_price=:entry,"
        "stop_loss=:sl,take_profit=:tp,timeframe=:tf,analysis=:anal,"
        "ai_confidence=:conf,status=:status WHERE id=:id",
        {"sym":data.symbol.upper(),"dir":data.direction.upper(),
         "entry":data.entry_price,"sl":data.stop_loss,"tp":data.take_profit,
         "tf":data.timeframe or "1H","anal":data.analysis or "",
         "conf":data.ai_confidence,"status":data.status or "active","id":sid}
    )
    return {"message": "Signal updated"}

@router.delete("/signals/{sid}")
async def cms_delete_signal(sid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM signals WHERE id=:id", {"id": sid})
    return {"message": "Signal deleted"}

@router.post("/signals/{sid}/close")
async def cms_close_signal(sid: int, outcome: Optional[str] = "closed", _=Depends(get_admin_user)):
    await _exec("UPDATE signals SET status='closed',outcome=:outcome WHERE id=:id",
                {"outcome": outcome, "id": sid})
    return {"message": f"Signal closed ({outcome})"}


# ══════════════════════════════════════════════════════════════════════════════
# WEBINARS  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

class WebinarIn(BaseModel):
    title: str
    description: Optional[str] = ""
    presenter: Optional[str] = ""
    scheduled_at: str
    duration_minutes: Optional[int] = 60
    meeting_link: Optional[str] = ""
    recording_url: Optional[str] = ""
    thumbnail: Optional[str] = ""
    max_attendees: Optional[int] = 100
    is_published: bool = False

@router.get("/webinars")
async def cms_list_webinars(_=Depends(get_admin_user)):
    rows = await _rows(
        "SELECT id,title,description,presenter,scheduled_at,duration_minutes,"
        "meeting_link,recording_url,thumbnail,max_attendees,is_published,status,created_at "
        "FROM webinars ORDER BY scheduled_at DESC"
    )
    for r in rows:
        r["scheduled_at"] = _fmt(r.get("scheduled_at"))
        r["created_at"]   = _fmt(r.get("created_at"))
    return rows

@router.post("/webinars", status_code=201)
async def cms_create_webinar(data: WebinarIn, _=Depends(get_admin_user)):
    try: sched = datetime.fromisoformat(data.scheduled_at.replace("Z", "+00:00"))
    except: raise HTTPException(400, "Invalid scheduled_at format")
    wid = await _exec(
        "INSERT INTO webinars (title,description,presenter,scheduled_at,duration_minutes,"
        "meeting_link,recording_url,thumbnail,max_attendees,is_published,status,created_at) "
        "VALUES (:title,:desc,:presenter,:sched,:dur,:link,:rec,:thumb,:max,:pub,:status,:now) RETURNING id",
        {"title":data.title,"desc":data.description or "","presenter":data.presenter or "",
         "sched":sched,"dur":data.duration_minutes or 60,"link":data.meeting_link or "",
         "rec":data.recording_url or "","thumb":data.thumbnail or "",
         "max":data.max_attendees or 100,"pub":data.is_published,
         "status":"scheduled" if data.is_published else "draft","now":datetime.utcnow()}
    )
    return {"id": wid, "message": "Webinar created"}

@router.put("/webinars/{wid}")
async def cms_update_webinar(wid: int, data: WebinarIn, _=Depends(get_admin_user)):
    if not await _row("SELECT id FROM webinars WHERE id=:id", {"id": wid}):
        raise HTTPException(404, "Webinar not found")
    try: sched = datetime.fromisoformat(data.scheduled_at.replace("Z", "+00:00"))
    except: raise HTTPException(400, "Invalid scheduled_at format")
    await _exec(
        "UPDATE webinars SET title=:title,description=:desc,presenter=:presenter,"
        "scheduled_at=:sched,duration_minutes=:dur,meeting_link=:link,recording_url=:rec,"
        "thumbnail=:thumb,max_attendees=:max,is_published=:pub,status=:status WHERE id=:id",
        {"title":data.title,"desc":data.description or "","presenter":data.presenter or "",
         "sched":sched,"dur":data.duration_minutes or 60,"link":data.meeting_link or "",
         "rec":data.recording_url or "","thumb":data.thumbnail or "",
         "max":data.max_attendees or 100,"pub":data.is_published,
         "status":"scheduled" if data.is_published else "draft","id":wid}
    )
    return {"message": "Webinar updated"}

@router.delete("/webinars/{wid}")
async def cms_delete_webinar(wid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM webinars WHERE id=:id", {"id": wid})
    return {"message": "Webinar deleted"}

@router.post("/webinars/{wid}/toggle-publish")
async def cms_toggle_webinar(wid: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id,is_published FROM webinars WHERE id=:id", {"id": wid})
    if not r: raise HTTPException(404, "Webinar not found")
    ns = not bool(r["is_published"])
    # Sync both is_published and legacy status column
    await _exec("UPDATE webinars SET is_published=:pub,status=:status WHERE id=:id",
                {"pub": ns, "status": "scheduled" if ns else "draft", "id": wid})
    return {"is_published": ns, "message": "Published" if ns else "Unpublished"}


# ══════════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

class UserRoleIn(BaseModel):
    role: str   # "admin" | "moderator" | "user"

class UserSubIn(BaseModel):
    subscription_tier: str   # "free" | "pro" | "enterprise"

class UserNoteIn(BaseModel):
    note: str

@router.get("/users")
async def cms_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    tier: Optional[str] = None,
    _=Depends(get_admin_user)
):
    where = []
    v = {}
    if search:
        where.append("(email ILIKE :search OR full_name ILIKE :search)")
        v["search"] = f"%{search}%"
    if role:
        where.append("role = :role")
        v["role"] = role
    if tier:
        where.append("subscription_tier = :tier")
        v["tier"] = tier

    where_clause = ("WHERE " + " AND ".join(where)) if where else ""
    offset = (page - 1) * per_page

    total = (await _row(f"SELECT COUNT(*) AS c FROM users {where_clause}", v) or {}).get("c", 0)
    rows = await _rows(
        f"SELECT id,email,full_name,is_active,is_admin,role,subscription_tier,"
        f"created_at,last_login FROM users {where_clause} "
        f"ORDER BY created_at DESC LIMIT {per_page} OFFSET {offset}",
        v
    )
    for r in rows:
        r["created_at"] = _fmt(r.get("created_at"))
        r["last_login"]  = _fmt(r.get("last_login"))
        # Derive display role
        if r.get("is_admin"): r["display_role"] = "admin"
        elif r.get("role"):   r["display_role"] = r["role"]
        else:                 r["display_role"] = "user"

    return {"users": rows, "total": total, "page": page,
            "per_page": per_page, "pages": max(1, (total + per_page - 1) // per_page)}

@router.post("/users/{uid}/role")
async def cms_set_user_role(uid: int, data: UserRoleIn, _=Depends(get_admin_user)):
    valid = {"admin", "moderator", "user"}
    if data.role not in valid:
        raise HTTPException(400, f"Role must be one of: {', '.join(valid)}")
    is_admin = data.role == "admin"
    await _exec(
        "UPDATE users SET role=:role, is_admin=:admin WHERE id=:id",
        {"role": data.role, "admin": is_admin, "id": uid}
    )
    return {"message": f"User role set to '{data.role}'"}

@router.post("/users/{uid}/subscription")
async def cms_set_subscription(uid: int, data: UserSubIn, _=Depends(get_admin_user)):
    valid = {"free", "pro", "enterprise"}
    if data.subscription_tier not in valid:
        raise HTTPException(400, f"Tier must be one of: {', '.join(valid)}")
    await _exec(
        "UPDATE users SET subscription_tier=:tier WHERE id=:id",
        {"tier": data.subscription_tier, "id": uid}
    )
    return {"message": f"Subscription set to '{data.subscription_tier}'"}

@router.post("/users/{uid}/toggle-active")
async def cms_toggle_user(uid: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id,is_active FROM users WHERE id=:id", {"id": uid})
    if not r: raise HTTPException(404, "User not found")
    ns = not bool(r["is_active"])
    await _exec("UPDATE users SET is_active=:active WHERE id=:id", {"active": ns, "id": uid})
    return {"is_active": ns, "message": "User activated" if ns else "User banned"}

@router.get("/users/{uid}/activity")
async def cms_user_activity(uid: int, _=Depends(get_admin_user)):
    """Aggregate a user's platform activity from multiple tables."""
    signal_count  = (await _row("SELECT COUNT(*) AS c FROM signals WHERE created_by=:uid", {"uid": uid}) or {}).get("c", 0)
    journal_count = (await _row("SELECT COUNT(*) AS c FROM journal_uploads WHERE user_id=:uid", {"uid": uid}) or {}).get("c", 0)
    mentor_count  = (await _row("SELECT COUNT(*) AS c FROM ai_mentor_logs WHERE user_id=:uid", {"uid": uid}) or {}).get("c", 0)
    chart_count   = (await _row("SELECT COUNT(*) AS c FROM chart_analysis_logs WHERE user_id=:uid", {"uid": uid}) or {}).get("c", 0)
    recent_logins = await _rows(
        "SELECT created_at FROM login_logs WHERE user_id=:uid ORDER BY created_at DESC LIMIT 10",
        {"uid": uid}
    )
    return {
        "signal_count":      int(signal_count  or 0),
        "journal_uploads":   int(journal_count or 0),
        "mentor_requests":   int(mentor_count  or 0),
        "charts_analyzed":   int(chart_count   or 0),
        "recent_logins":     [_fmt(r.get("created_at")) for r in recent_logins],
    }


# ══════════════════════════════════════════════════════════════════════════════
# ANNOUNCEMENTS / BANNERS
# ══════════════════════════════════════════════════════════════════════════════

class AnnouncementIn(BaseModel):
    message: str
    type: Optional[str] = "info"    # info | warning | success | danger
    is_active: bool = True
    expires_at: Optional[str] = ""

@router.get("/announcements")
async def cms_list_announcements(_=Depends(get_admin_user)):
    rows = await _rows("SELECT * FROM announcements ORDER BY created_at DESC")
    for r in rows:
        r["created_at"] = _fmt(r.get("created_at"))
        r["expires_at"] = _fmt(r.get("expires_at"))
    return rows

@router.post("/announcements", status_code=201)
async def cms_create_announcement(data: AnnouncementIn, _=Depends(get_admin_user)):
    exp = None
    if data.expires_at:
        try: exp = datetime.fromisoformat(data.expires_at.replace("Z", "+00:00"))
        except: pass
    aid = await _exec(
        "INSERT INTO announcements (message,type,is_active,expires_at,created_at) "
        "VALUES (:msg,:type,:active,:exp,:now) RETURNING id",
        {"msg":data.message,"type":data.type or "info","active":data.is_active,
         "exp":exp,"now":datetime.utcnow()}
    )
    return {"id": aid, "message": "Announcement created"}

@router.delete("/announcements/{aid}")
async def cms_delete_announcement(aid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM announcements WHERE id=:id", {"id": aid})
    return {"message": "Announcement deleted"}

@router.post("/announcements/{aid}/toggle")
async def cms_toggle_announcement(aid: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id,is_active FROM announcements WHERE id=:id", {"id": aid})
    if not r: raise HTTPException(404, "Announcement not found")
    ns = not bool(r["is_active"])
    await _exec("UPDATE announcements SET is_active=:a WHERE id=:id", {"a": ns, "id": aid})
    return {"is_active": ns}


# ══════════════════════════════════════════════════════════════════════════════
# COUPONS
# ══════════════════════════════════════════════════════════════════════════════

class CouponIn(BaseModel):
    code: str
    discount_type: str       # "percent" | "fixed"
    discount_value: float
    max_uses: Optional[int] = 100
    expires_at: Optional[str] = ""
    is_active: bool = True

@router.get("/coupons")
async def cms_list_coupons(_=Depends(get_admin_user)):
    rows = await _rows("SELECT * FROM coupons ORDER BY created_at DESC")
    for r in rows:
        r["created_at"] = _fmt(r.get("created_at"))
        r["expires_at"] = _fmt(r.get("expires_at"))
    return rows

@router.post("/coupons", status_code=201)
async def cms_create_coupon(data: CouponIn, _=Depends(get_admin_user)):
    if await _row("SELECT id FROM coupons WHERE code=:code", {"code": data.code.upper()}):
        raise HTTPException(400, "Coupon code already exists")
    exp = None
    if data.expires_at:
        try: exp = datetime.fromisoformat(data.expires_at.replace("Z", "+00:00"))
        except: pass
    cid = await _exec(
        "INSERT INTO coupons (code,discount_type,discount_value,max_uses,uses,expires_at,is_active,created_at) "
        "VALUES (:code,:type,:val,:max,0,:exp,:active,:now) RETURNING id",
        {"code":data.code.upper(),"type":data.discount_type,"val":data.discount_value,
         "max":data.max_uses or 100,"exp":exp,"active":data.is_active,"now":datetime.utcnow()}
    )
    return {"id": cid, "message": "Coupon created"}

@router.delete("/coupons/{cid}")
async def cms_delete_coupon(cid: int, _=Depends(get_admin_user)):
    await _exec("DELETE FROM coupons WHERE id=:id", {"id": cid})
    return {"message": "Coupon deleted"}

@router.post("/coupons/{cid}/toggle")
async def cms_toggle_coupon(cid: int, _=Depends(get_admin_user)):
    r = await _row("SELECT id,is_active FROM coupons WHERE id=:id", {"id": cid})
    if not r: raise HTTPException(404, "Coupon not found")
    ns = not bool(r["is_active"])
    await _exec("UPDATE coupons SET is_active=:a WHERE id=:id", {"a": ns, "id": cid})
    return {"is_active": ns}


# ══════════════════════════════════════════════════════════════════════════════
# SITE SETTINGS  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

_CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS site_settings (
    key VARCHAR(120) PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
)"""

_DEFAULT_SETTINGS = {
    "site_name": "Pipways", "site_tagline": "Professional Trading Platform",
    "contact_email": "support@pipways.com", "support_email": "support@pipways.com",
    "twitter_url": "", "instagram_url": "", "telegram_url": "",
    "youtube_url": "", "discord_url": "", "logo_url": "", "favicon_url": "",
    "maintenance_mode": "false", "allow_registration": "true",
    "free_signals_limit": "3", "currency": "USD", "timezone": "UTC",
    "analytics_id": "", "smtp_host": "", "smtp_port": "587", "smtp_user": "",
    "footer_text": "© 2025 Pipways. All rights reserved.",
}

async def _ensure_settings_table():
    try:
        await database.execute(_CREATE_SETTINGS_TABLE)
        for k, v in _DEFAULT_SETTINGS.items():
            await database.execute(
                "INSERT INTO site_settings (key,value,updated_at) VALUES (:k,:v,NOW()) "
                "ON CONFLICT (key) DO NOTHING", {"k": k, "v": v}
            )
    except Exception as e:
        print(f"[CMS] settings init: {e}", flush=True)

@router.get("/settings")
async def cms_get_settings(_=Depends(get_admin_user)):
    await _ensure_settings_table()
    rows = await _rows("SELECT key,value FROM site_settings ORDER BY key")
    return {r["key"]: r["value"] for r in rows}

@router.put("/settings")
async def cms_update_settings(updates: dict, _=Depends(get_admin_user)):
    await _ensure_settings_table()
    now = datetime.utcnow()
    for k, v in updates.items():
        if not isinstance(k, str) or len(k) > 120: continue
        await _exec(
            "INSERT INTO site_settings (key,value,updated_at) VALUES (:k,:v,:now) "
            "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value,updated_at=EXCLUDED.updated_at",
            {"k": k, "v": str(v), "now": now}
        )
    return {"message": f"Saved {len(updates)} setting(s)"}
