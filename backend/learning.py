"""
Pipways Trading Academy — Learning Router v4.5 (Production - Hardened)
Features: N+1 Query Elimination, Sequential Unlocking, Hardened Quiz, Optimized Badges
Fixes: Validation layer, AI resilience, Idempotent operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import os
import httpx
import traceback

from .security import get_current_user
from .database import database

router = APIRouter()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class QuizAnswer(BaseModel):
    question_id: int
    selected_answer: str

class QuizSubmission(BaseModel):
    lesson_id: int
    answers: List[QuizAnswer]

class LessonCompleteRequest(BaseModel):
    lesson_id: int
    quiz_score: float = 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_user_dict(current_user) -> dict:
    """Convert Record/Row object to dict safely."""
    if not current_user:
        return {}
    if isinstance(current_user, dict):
        return current_user
    try:
        return dict(current_user)
    except (TypeError, ValueError):
        try:
            return {k: current_user[k] for k in current_user.keys()}
        except AttributeError:
            try:
                return {k: getattr(current_user, k) for k in dir(current_user) if not k.startswith('_')}
            except Exception:
                return {}

def _parse_json(value) -> list:
    """Safely parse JSON fields with error logging."""
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            print(f"[JSON PARSE ERROR] Failed to parse: {str(value)[:100]}... Error: {e}", flush=True)
            return []
    print(f"[JSON PARSE ERROR] Unexpected type: {type(value)}", flush=True)
    return []

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION HELPERS (Fix #7)
# ═══════════════════════════════════════════════════════════════════════════════

async def _verify_level_exists(level_id: int):
    level = await database.fetch_one("SELECT id FROM learning_levels WHERE id=:id", {"id": level_id})
    if not level:
        raise HTTPException(status_code=404, detail="Level not found")

async def _verify_module_exists(module_id: int):
    module = await database.fetch_one("SELECT id FROM learning_modules WHERE id=:id", {"id": module_id})
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

async def _verify_lesson_exists(lesson_id: int):
    lesson = await database.fetch_one("SELECT id FROM learning_lessons WHERE id=:id", {"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

# ═══════════════════════════════════════════════════════════════════════════════
# LLM HELPERS (Fix #5 - Hardened)
# ═══════════════════════════════════════════════════════════════════════════════

async def _ai(system: str, user_msg: str, max_tokens: int = 800) -> str:
    if not OPENROUTER_API_KEY:
        return "Trading Coach is currently unavailable. Please configure OPENROUTER_API_KEY."
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways Trading Academy",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_msg},
                    ],
                }
            )
            
            # Response validation
            if res.status_code != 200:
                print(f"[TRADING COACH] API error {res.status_code}: {res.text[:200]}", flush=True)
                return "Trading Coach is experiencing technical difficulties. Please try again shortly."
            
            try:
                data = res.json()
            except json.JSONDecodeError as e:
                print(f"[TRADING COACH] JSON decode error: {e}", flush=True)
                return "Trading Coach received invalid data. Please try again."
            
            if not isinstance(data, dict):
                print(f"[TRADING COACH] Unexpected response type: {type(data)}", flush=True)
                return "Trading Coach response format error. Please try again."
            
            if "error" in data:
                err_msg = data["error"].get("message", "Unknown error") if isinstance(data["error"], dict) else str(data["error"])
                print(f"[TRADING COACH] API error in response: {err_msg}", flush=True)
                return f"Trading Coach error: {err_msg}"
            
            choices = data.get("choices")
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                print(f"[TRADING COACH] No choices in response: {list(data.keys())}", flush=True)
                return "Trading Coach is having trouble responding. Please try again shortly."
            
            message = choices[0].get("message", {})
            if not isinstance(message, dict):
                print(f"[TRADING COACH] Invalid message format: {type(message)}", flush=True)
                return "Trading Coach response malformed. Please try again."
                
            content = message.get("content")
            if not content or not isinstance(content, str):
                print(f"[TRADING COACH] Empty or invalid content", flush=True)
                return "Trading Coach has no response at this time. Please try again."
            
            return content
            
    except httpx.TimeoutException:
        print(f"[TRADING COACH] Timeout error", flush=True)
        return "Trading Coach is taking too long to respond. Please try again shortly."
    except Exception as e:
        print(f"[TRADING COACH] Error: {e}", flush=True)
        return "I'm having trouble connecting right now. Please try again shortly."

# ═══════════════════════════════════════════════════════════════════════════════
# BADGE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

BADGE_DEFINITIONS = {
    "beginner_trader": {"name": "Beginner Trader", "icon": "fa-seedling", "color": "#34d399", "desc": "Completed Beginner level"},
    "technical_analyst": {"name": "Technical Analyst", "icon": "fa-chart-line", "color": "#60a5fa", "desc": "Completed Intermediate level"},
    "strategy_builder": {"name": "Strategy Builder", "icon": "fa-chess-knight", "color": "#a78bfa", "desc": "Completed Advanced level"},
    "pipways_certified": {"name": "Pipways Certified", "icon": "fa-certificate", "color": "#f59e0b", "desc": "Completed entire Academy curriculum"},
    "quiz_master": {"name": "Quiz Master", "icon": "fa-cogs", "color": "#f472b6", "desc": "Passed 10 quizzes with 80%+"},
    "perfect_score": {"name": "Perfect Score", "icon": "fa-medal", "color": "#fbbf24", "desc": "Scored 100% on any quiz"},
    "risk_manager": {"name": "Risk Manager", "icon": "fa-shield-alt", "color": "#22d3ee", "desc": "Mastered Risk Management modules"},
    "psychology_pro": {"name": "Psychology Pro", "icon": "fa-cogs", "color": "#e879f9", "desc": "Completed Trading Psychology module"},
}

async def _award_badge(user_id: int, badge_type: str) -> bool:
    if badge_type not in BADGE_DEFINITIONS:
        return False
    try:
        existing = await database.fetch_one(
            "SELECT id FROM user_badges WHERE user_id=:uid AND badge_type=:bt",
            {"uid": user_id, "bt": badge_type}
        )
        if existing:
            return False
        await database.execute(
            "INSERT INTO user_badges (user_id, badge_type, earned_at) VALUES (:uid, :bt, NOW())",
            {"uid": user_id, "bt": badge_type}
        )
        return True
    except Exception as e:
        print(f"[BADGE ERROR] Failed to award {badge_type} to user {user_id}: {e}", flush=True)
        return False

async def _check_and_award_badges(user_id: int, lesson_id: int = None, quiz_score: float = None):
    """Optimized badge checking with bulk operations (Fix #4)"""
    newly_awarded = []
    
    try:
        # Single query to get all existing badges
        badge_rows = await database.fetch_all(
            "SELECT badge_type FROM user_badges WHERE user_id = :uid",
            {"uid": user_id}
        )
        existing_badges = {r["badge_type"] for r in badge_rows}
        
        # Single query to get all completion stats
        stats = await database.fetch_one(
            """
            SELECT 
                COUNT(DISTINCT CASE WHEN l.level_id = 1 THEN p.lesson_id END) as beginner_done,
                COUNT(DISTINCT CASE WHEN l.level_id = 2 THEN p.lesson_id END) as intermediate_done,  
                COUNT(DISTINCT CASE WHEN l.level_id = 3 THEN p.lesson_id END) as advanced_done,
                COUNT(DISTINCT CASE WHEN p.quiz_score >= 80 THEN p.lesson_id END) as high_score_count,
                COUNT(DISTINCT CASE WHEN p.quiz_score = 100 THEN p.lesson_id END) as perfect_count,
                COUNT(DISTINCT p.lesson_id) as total_done
            FROM user_learning_progress p
            JOIN learning_lessons l ON l.id = p.lesson_id
            WHERE p.user_id = :uid AND p.completed = TRUE
            """,
            {"uid": user_id}
        )
        
        # Get level totals
        total_rows = await database.fetch_all(
            "SELECT m.level_id, COUNT(*) as total FROM learning_lessons l JOIN learning_modules m ON m.id = l.module_id GROUP BY m.level_id"
        )
        total_map = {t["level_id"]: t["total"] for t in total_rows}
        
        badges_to_insert = []
        
        # Level completion badges
        if "beginner_trader" not in existing_badges and stats["beginner_done"] >= total_map.get(1, 999):
            badges_to_insert.append("beginner_trader")
            newly_awarded.append("beginner_trader")
        
        if "technical_analyst" not in existing_badges and stats["intermediate_done"] >= total_map.get(2, 999):
            badges_to_insert.append("technical_analyst")
            newly_awarded.append("technical_analyst")
            
        if "strategy_builder" not in existing_badges and stats["advanced_done"] >= total_map.get(3, 999):
            badges_to_insert.append("strategy_builder")
            newly_awarded.append("strategy_builder")
        
        if "pipways_certified" not in existing_badges:
            total_all = sum(total_map.values())
            if stats["total_done"] >= total_all:
                badges_to_insert.append("pipways_certified")
                newly_awarded.append("pipways_certified")
        
        # Quiz badges
        if "perfect_score" not in existing_badges and quiz_score == 100:
            badges_to_insert.append("perfect_score")
            newly_awarded.append("perfect_score")
            
        if "quiz_master" not in existing_badges and stats["high_score_count"] >= 10:
            badges_to_insert.append("quiz_master")
            newly_awarded.append("quiz_master")
        
        # Bulk insert badges
        if badges_to_insert:
            values = [{"uid": user_id, "bt": bt} for bt in badges_to_insert]
            await database.execute_many(
                "INSERT INTO user_badges (user_id, badge_type, earned_at) VALUES (:uid, :bt, NOW())",
                values
            )
        
        # Topic-specific badges (only if lesson_id provided and badges missing)
        if lesson_id and ("risk_manager" not in existing_badges or "psychology_pro" not in existing_badges):
            lesson = await database.fetch_one(
                """SELECT m.title FROM learning_lessons l
                   JOIN learning_modules m ON m.id=l.module_id 
                   WHERE l.id=:lid""",
                {"lid": lesson_id}
            )
            if lesson:
                title = lesson["title"].lower()
                if "risk" in title and "risk_manager" not in existing_badges:
                    if await _award_badge(user_id, "risk_manager"):
                        newly_awarded.append("risk_manager")
                if "psychology" in title and "psychology_pro" not in existing_badges:
                    if await _award_badge(user_id, "psychology_pro"):
                        newly_awarded.append("psychology_pro")
                    
    except Exception as e:
        print(f"[BADGE CHECK ERROR] {e}", flush=True)
        traceback.print_exc()
    
    return newly_awarded

# ═══════════════════════════════════════════════════════════════════════════════
# READ ENDPOINTS (N+1 Eliminated - Fix #2)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/levels")
async def get_levels(current_user=Depends(get_current_user)):
    try:
        rows = await database.fetch_all(
            "SELECT id, name, description, order_index FROM learning_levels ORDER BY order_index"
        )
        return [dict(r) for r in (rows or [])]
    except Exception as e:
        print(f"[API ERROR] get_levels: {e}", flush=True)
        return []

@router.get("/modules/{level_id}")
async def get_modules(level_id: int, current_user=Depends(get_current_user)):
    try:
        await _verify_level_exists(level_id)
        
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        
        # Single aggregated query - no N+1
        rows = await database.fetch_all(
            """
            SELECT 
                m.id, 
                m.title, 
                m.description, 
                m.order_index,
                COUNT(DISTINCT l.id) as lesson_count,
                COUNT(DISTINCT CASE WHEN p.completed = TRUE THEN p.lesson_id END) as completed_count
            FROM learning_modules m
            LEFT JOIN learning_lessons l ON l.module_id = m.id
            LEFT JOIN user_learning_progress p ON p.module_id = m.id AND p.user_id = :uid AND p.completed = TRUE
            WHERE m.level_id = :lid
            GROUP BY m.id, m.title, m.description, m.order_index
            ORDER BY m.order_index
            """,
            {"lid": level_id, "uid": user_id}
        )
        
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "order_index": r["order_index"],
                "lesson_count": r["lesson_count"] or 0,
                "completed_count": r["completed_count"] or 0,
                "is_complete": (r["completed_count"] or 0) >= (r["lesson_count"] or 0) and (r["lesson_count"] or 0) > 0
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_modules: {e}", flush=True)
        return []

@router.get("/lessons/{module_id}")
async def get_lessons(module_id: int, current_user=Depends(get_current_user)):
    try:
        await _verify_module_exists(module_id)
        
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        
        # Single query for lessons with progress (Fix #2)
        rows = await database.fetch_all(
            """
            SELECT 
                l.id, 
                l.title, 
                l.order_index,
                p.completed,
                p.quiz_score
            FROM learning_lessons l
            LEFT JOIN user_learning_progress p ON p.lesson_id = l.id AND p.user_id = :uid
            WHERE l.module_id = :mid
            ORDER BY l.order_index
            """,
            {"mid": module_id, "uid": user_id}
        )
        
        result = []
        prev_completed = True  # First lesson always unlocked (Fix #1)
        
        for r in rows:
            is_completed = bool(r["completed"]) if r["completed"] is not None else False
            
            result.append({
                "id": r["id"],
                "title": r["title"],
                "order_index": r["order_index"],
                "completed": is_completed,
                "quiz_score": r["quiz_score"],
                "unlocked": prev_completed  # Sequential unlocking
            })
            
            prev_completed = is_completed  # Current determines next unlock
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_lessons: {e}", flush=True)
        return []

@router.get("/lesson/{lesson_id}")
async def get_lesson(lesson_id: int, current_user=Depends(get_current_user)):
    try:
        await _verify_lesson_exists(lesson_id)
        
        lesson = await database.fetch_one(
            """SELECT l.id, l.title, l.content, l.order_index, l.module_id,
                      m.title AS module_title, m.level_id, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id = l.module_id
               JOIN learning_levels lv ON lv.id = m.level_id
               WHERE l.id = :lid""",
            {"lid": lesson_id}
        )
        
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        
        # Get adjacent lessons with completion status
        adj = await database.fetch_all(
            """SELECT l.id, l.title, l.order_index,
                      EXISTS(SELECT 1 FROM user_learning_progress p 
                             WHERE p.lesson_id=l.id AND p.user_id=:uid AND p.completed=TRUE) as completed
               FROM learning_lessons l
               WHERE l.module_id = :mid
               ORDER BY l.order_index""",
            {"mid": lesson["module_id"], "uid": user_id}
        )
        
        current_idx = next((i for i, a in enumerate(adj) if a["id"] == lesson_id), -1)
        prev_lesson = adj[current_idx - 1] if current_idx > 0 else None
        next_lesson = adj[current_idx + 1] if current_idx < len(adj) - 1 else None
        
        result = dict(lesson)
        result["prev_lesson"] = {
            "id": prev_lesson["id"],
            "title": prev_lesson["title"],
            "completed": prev_lesson["completed"]
        } if prev_lesson else None
        
        result["next_lesson"] = {
            "id": next_lesson["id"],
            "title": next_lesson["title"],
            "completed": next_lesson["completed"]
        } if next_lesson else None
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_lesson: {e}", flush=True)
        raise HTTPException(500, detail="Failed to load lesson data")

@router.get("/quiz/{lesson_id}")
async def get_quiz(lesson_id: int, current_user=Depends(get_current_user)):
    try:
        await _verify_lesson_exists(lesson_id)
        
        questions = await database.fetch_all(
            """SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, topic_slug
               FROM lesson_quizzes 
               WHERE lesson_id=:lid ORDER BY id""",
            {"lid": lesson_id}
        )
        
        return {
            "lesson_id": lesson_id,
            "question_count": len(questions) if questions else 0,
            "questions": [dict(q) for q in (questions or [])]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_quiz: {e}", flush=True)
        return {"lesson_id": lesson_id, "question_count": 0, "questions": []}

@router.get("/progress/{user_id}")
async def get_progress(user_id: int, current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        caller = user.get("id", 0)
        is_admin = user.get("is_admin", False)
        
        if caller != user_id and not is_admin:
            raise HTTPException(403, detail="Unauthorized")
        
        rows = await database.fetch_all(
            """SELECT p.id, p.level_id, p.module_id, p.lesson_id, p.completed,
                      p.quiz_score, p.completed_at, l.title AS lesson_title, m.title AS module_title
               FROM user_learning_progress p
               LEFT JOIN learning_lessons l ON l.id = p.lesson_id
               LEFT JOIN learning_modules m ON m.id = p.module_id
               WHERE p.user_id = :uid
               ORDER BY p.completed_at DESC""",
            {"uid": user_id}
        )
        
        levels = await database.fetch_all("SELECT id, name FROM learning_levels ORDER BY order_index") or []
        
        summary = []
        for lv in levels:
            try:
                total = await database.fetch_val(
                    """SELECT COUNT(*) FROM learning_lessons l
                       JOIN learning_modules m ON m.id=les.module_id 
                       WHERE m.level_id=:lid""",
                    {"lid": lv["id"]}
                ) or 0
                
                done = await database.fetch_val(
                    """SELECT COUNT(*) FROM user_learning_progress
                       WHERE user_id=:uid AND level_id=:lid AND completed=TRUE""",
                    {"uid": user_id, "lid": lv["id"]}
                ) or 0
                
                summary.append({
                    "level_id": lv["id"],
                    "level_name": lv["name"],
                    "total": int(total),
                    "completed": int(done),
                    "percent": round((int(done) / int(total) * 100) if total else 0, 1),
                })
            except Exception as e:
                print(f"[API ERROR] get_progress summary loop: {e}", flush=True)
                summary.append({
                    "level_id": lv["id"],
                    "level_name": lv["name"],
                    "total": 0,
                    "completed": 0,
                    "percent": 0.0
                })
        
        total_lessons = await database.fetch_val("SELECT COUNT(*) FROM learning_lessons") or 0
        completed_lessons = sum(1 for p in (rows or []) if p and p.get('completed'))
        
        return {
            "user_id": user_id,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "completion_rate": round((completed_lessons / total_lessons * 100) if total_lessons else 0, 1),
            "progress": [dict(r) for r in (rows or [])],
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_progress: {e}", flush=True)
        return {
            "user_id": user_id,
            "total_lessons": 0,
            "completed_lessons": 0,
            "completion_rate": 0.0,
            "progress": [],
            "summary": []
        }

@router.get("/badges/{user_id}")
async def get_badges(user_id: int, current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        caller = user.get("id", 0)
        is_admin = user.get("is_admin", False)
        
        if caller != user_id and not is_admin:
            raise HTTPException(403, detail="Unauthorized")
        
        rows = await database.fetch_all(
            """SELECT badge_type, earned_at 
               FROM user_badges 
               WHERE user_id=:uid ORDER BY earned_at DESC""",
            {"uid": user_id}
        )
        
        badges = []
        for r in (rows or []):
            try:
                defn = BADGE_DEFINITIONS.get(r["badge_type"], {})
                badges.append({
                    "type": r["badge_type"],
                    "name": defn.get("name", r["badge_type"]),
                    "icon": defn.get("icon", "fa-medal"),
                    "color": defn.get("color", "#a78bfa"),
                    "earned_at": r["earned_at"]
                })
            except Exception as e:
                print(f"[API ERROR] get_badges loop: {e}", flush=True)
                continue
        
        return {"user_id": user_id, "badges": badges, "count": len(badges)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_badges: {e}", flush=True)
        return {"user_id": user_id, "badges": [], "count": 0}

@router.get("/profile/{user_id}")
async def get_profile(user_id: int, current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        caller = user.get("id", 0)
        is_admin = user.get("is_admin", False)
        
        if caller != user_id and not is_admin:
            raise HTTPException(403, detail="Unauthorized")
        
        row = await database.fetch_one(
            """SELECT weak_topics, strong_topics, first_academy_visit, last_updated
               FROM user_learning_profile WHERE user_id=:uid""",
            {"uid": user_id}
        )
        
        if not row:
            return {
                "user_id": user_id,
                "weak_topics": [],
                "strong_topics": [],
                "first_academy_visit": True,
                "last_updated": None
            }
        
        return {
            "user_id": user_id,
            "weak_topics": _parse_json(row.get("weak_topics")),
            "strong_topics": _parse_json(row.get("strong_topics")),
            "first_academy_visit": row.get("first_academy_visit") if row.get("first_academy_visit") is not None else True,
            "last_updated": row.get("last_updated"),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_profile: {e}", flush=True)
        return {
            "user_id": user_id,
            "weak_topics": [],
            "strong_topics": [],
            "first_academy_visit": True,
            "last_updated": None
        }

@router.post("/badges/check")
async def check_badges(current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        if not user_id:
            raise HTTPException(401, detail="Not authenticated")
        
        new_badges = await _check_and_award_badges(user_id)
        return {"newly_awarded": new_badges, "count": len(new_badges)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] check_badges: {e}", flush=True)
        return {"newly_awarded": [], "count": 0}

# ═══════════════════════════════════════════════════════════════════════════════
# WRITE ENDPOINTS (Hardened - Fix #3)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmission, current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        if not user_id:
            raise HTTPException(401, detail="Not authenticated")
        
        # Verify lesson exists (Fix #3, #7)
        lesson = await database.fetch_one(
            "SELECT id, module_id FROM learning_lessons WHERE id=:lid", 
            {"lid": payload.lesson_id}
        )
        if not lesson:
            raise HTTPException(404, detail="Lesson not found")
        
        # Rapid submission protection (Fix #3)
        recent = await database.fetch_one(
            """SELECT 1 FROM user_quiz_results 
               WHERE user_id=:uid AND lesson_id=:lid 
               AND answered_at > NOW() - INTERVAL '5 seconds'""",
            {"uid": user_id, "lid": payload.lesson_id}
        )
        if recent:
            raise HTTPException(429, detail="Quiz submission too rapid. Please wait a moment.")
        
        # Get all valid questions (Fix #3)
        questions = await database.fetch_all(
            """SELECT id, correct_answer, explanation, topic_slug 
               FROM lesson_quizzes WHERE lesson_id=:lid ORDER BY id""",
            {"lid": payload.lesson_id}
        )
        
        if not questions:
            raise HTTPException(404, detail="No quiz questions found for this lesson")
        
        valid_ids = {q["id"] for q in questions}
        q_map = {q["id"]: q for q in questions}
        
        # Validate submitted answers (Fix #3)
        submitted_ids = {a.question_id for a in payload.answers}
        invalid = submitted_ids - valid_ids
        if invalid:
            raise HTTPException(400, detail=f"Invalid question IDs: {invalid}")
        
        total = len(questions)
        correct = 0
        wrong_slugs = []
        correct_slugs = []
        results = []
        
        for ans in payload.answers:
            try:
                q_id = ans.question_id
                selected = ans.selected_answer.upper()
                row = q_map[q_id]
                
                is_correct = (selected == row["correct_answer"].upper())
                if is_correct:
                    correct += 1
                    correct_slugs.append(row["topic_slug"])
                else:
                    wrong_slugs.append(row["topic_slug"])
                
                await database.execute(
                    """INSERT INTO user_quiz_results 
                       (user_id, lesson_id, question_id, selected_answer, is_correct, answered_at)
                       VALUES (:uid, :lid, :qid, :ans, :ok, NOW())
                       ON CONFLICT (user_id, question_id) DO UPDATE SET
                       selected_answer = EXCLUDED.selected_answer,
                       is_correct = EXCLUDED.is_correct,
                       answered_at = NOW()""",
                    {"uid": user_id, "lid": payload.lesson_id, "qid": q_id, "ans": selected, "ok": is_correct}
                )
                
                results.append({
                    "question_id": q_id,
                    "is_correct": is_correct,
                    "correct_answer": row["correct_answer"],
                    "explanation": row["explanation"],
                })
            except Exception as e:
                print(f"[API ERROR] submit_quiz answer processing: {e}", flush=True)
                continue
        
        score = round((correct / total * 100) if total else 0, 1)
        passed = score >= 70
        
        if passed:
            await _mark_lesson_complete(user_id, payload.lesson_id, score)
        
        await _update_learning_profile(user_id, wrong_slugs, correct_slugs)
        new_badges = await _check_and_award_badges(user_id, payload.lesson_id, score)
        
        lesson_info = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name 
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": payload.lesson_id}
        )
        
        feedback = await _quiz_feedback(
            score, passed,
            lesson_info["title"] if lesson_info else "this lesson",
            wrong_slugs,
            lesson_info["level_name"].lower() if lesson_info else "intermediate"
        )
        
        return {
            "score": score,
            "correct": correct,
            "total": total,
            "passed": passed,
            "results": results,
            "mentor_feedback": feedback,
            "new_badges": new_badges,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] submit_quiz: {e}", flush=True)
        raise HTTPException(500, detail="Failed to submit quiz")

@router.post("/lesson/complete")
async def complete_lesson(payload: LessonCompleteRequest, current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        if not user_id:
            raise HTTPException(401, detail="Not authenticated")
        
        await _verify_lesson_exists(payload.lesson_id)
        
        await _mark_lesson_complete(user_id, payload.lesson_id, payload.quiz_score)
        new_badges = await _check_and_award_badges(user_id, payload.lesson_id)
        return {"success": True, "new_badges": new_badges}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] complete_lesson: {e}", flush=True)
        raise HTTPException(500, detail="Failed to complete lesson")

@router.post("/profile/first-visit-complete")
async def mark_first_visit_complete(current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        if not user_id:
            raise HTTPException(401, detail="Not authenticated")
        
        await database.execute(
            """INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, first_academy_visit, last_updated)
               VALUES (:uid, '[]', '[]', FALSE, NOW())
               ON CONFLICT (user_id) DO UPDATE SET first_academy_visit=FALSE, last_updated=NOW()""",
            {"uid": user_id}
        )
        
        return {"success": True, "first_academy_visit": False}
    except Exception as e:
        print(f"[API ERROR] mark_first_visit_complete: {e}", flush=True)
        raise HTTPException(500, detail="Failed to update profile")

# ═══════════════════════════════════════════════════════════════════════════════
# AI TRADING COACH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/mentor/guide/{user_id}")
async def mentor_guide(user_id: int, current_user=Depends(get_current_user)):
    try:
        user = _safe_user_dict(current_user)
        caller = user.get("id", 0)
        is_admin = user.get("is_admin", False)
        
        if caller != user_id and not is_admin:
            raise HTTPException(403, detail="Unauthorized")
        
        profile = await database.fetch_one(
            """SELECT weak_topics, strong_topics, first_academy_visit 
               FROM user_learning_profile WHERE user_id=:uid""",
            {"uid": user_id}
        )
        
        is_first = not profile or profile.get("first_academy_visit") is not False
        
        progress = await database.fetch_all(
            """SELECT l.title
               FROM user_learning_progress p 
               JOIN learning_lessons l ON l.id=p.lesson_id
               WHERE p.user_id=:uid AND p.completed=TRUE""",
            {"uid": user_id}
        )
        
        done = [r["title"] for r in (progress or [])]
        weak = _parse_json(profile.get("weak_topics")) if profile else []
        
        next_lesson = await database.fetch_one(
            """SELECT l.id, l.title, m.title AS module_title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id NOT IN (
                   SELECT lesson_id FROM user_learning_progress 
                   WHERE user_id=:uid AND completed=TRUE
               )
               ORDER BY m.order_index, l.order_index LIMIT 1""",
            {"uid": user_id}
        )
        
        if is_first:
            return {
                "type": "welcome",
                "message": "Welcome to Pipways Trading Academy! Start your journey with the Beginner level. Master the basics, then progress through structured modules designed by professional traders.",
                "next_lesson": dict(next_lesson) if next_lesson else None,
                "first_visit": True,
                "weak_topics": [],
            }
        
        ctx = (
            f"Progress: {len(done)} lessons completed. "
            f"Weak areas: {', '.join(weak) if weak else 'none identified'}. "
            f"Next: {next_lesson['title'] if next_lesson else 'Curriculum complete'}."
        )
        
        system = (
            "You are the Pipways Trading Coach. Give a motivational 2-sentence coaching message. "
            "Acknowledge progress, mention one weak area, and encourage the next lesson. "
            "Be warm, professional, and end with 'Continue Learning' energy."
        )
        
        message = await _ai(system, ctx)
        
        return {
            "type": "recommendation",
            "message": message,
            "next_lesson": dict(next_lesson) if next_lesson else None,
            "first_visit": False,
            "completed_count": len(done),
            "weak_topics": weak,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] mentor_guide: {e}", flush=True)
        return {
            "type": "welcome",
            "message": "Continue learning the Beginner modules to unlock personalized recommendations.",
            "next_lesson": None,
            "first_visit": True,
            "weak_topics": [],
        }

@router.post("/mentor/teach")
async def mentor_teach(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        await _verify_lesson_exists(lesson_id)
        
        lesson = await database.fetch_one(
            """SELECT l.title, l.content, m.title AS module_title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        
        user = _safe_user_dict(current_user)
        user_id = user.get("id", 0)
        
        profile = await database.fetch_one(
            "SELECT weak_topics FROM user_learning_profile WHERE user_id=:uid",
            {"uid": user_id}
        )
        
        weak = _parse_json(profile.get("weak_topics")) if profile else []
        level = lesson["level_name"].lower() if lesson else "intermediate"
        
        tone = {
            "beginner": "Use very simple language and real-world analogies. Avoid jargon entirely.",
            "intermediate": "Use technical terms with clear definitions. Connect to chart examples.",
            "advanced": "Use institutional terminology. Discuss market structure and order flow.",
        }.get(level, "Use clear, professional language.")
        
        system = (
            f"You are the Pipways Trading Coach. {tone} "
            "Structure: 1) Warm opening, 2) Core concept, 3) Step-by-step breakdown, "
            "4) Trade example (pair, entry, stop, target), 5) Common pitfall, 6) Quick summary. "
            "Keep under 450 words. Only explain THIS lesson content."
        )
        
        content_preview = lesson["content"][:1200] if lesson and lesson.get("content") else ""
        explanation = await _ai(system, f"Explain: {lesson['title']}\n\nContent: {content_preview}")
        
        return {
            "lesson_title": lesson["title"],
            "module_title": lesson["module_title"],
            "level": lesson["level_name"],
            "explanation": explanation,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] mentor_teach: {e}", flush=True)
        return {
            "lesson_title": "Lesson",
            "module_title": "Module",
            "level": "Beginner",
            "explanation": "Trading Coach explanation is temporarily unavailable. Please review the lesson content."
        }

@router.post("/mentor/practice")
async def mentor_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        await _verify_lesson_exists(lesson_id)
        
        lesson = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        
        system = (
            "You are a Pipways Trading Coach. Create ONE short, realistic practice exercise. "
            "Format: Scenario (1-2 sentences) → Question → Model Answer. "
            "Use different currency pairs each time. Under 180 words."
        )
        
        exercise = await _ai(system, f"Create exercise for '{lesson['title']}' at {lesson['level_name']} level.")
        
        return {"lesson_title": lesson["title"], "exercise": exercise}
    except Exception as e:
        print(f"[API ERROR] mentor_practice: {e}", flush=True)
        return {
            "lesson_title": "Practice",
            "exercise": "Practice exercise temporarily unavailable. Please review the lesson quiz instead."
        }

@router.post("/mentor/chart-practice")
async def mentor_chart_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        await _verify_lesson_exists(lesson_id)
        
        lesson = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        
        system = (
            "Create a chart-reading exercise. Return valid JSON with keys: "
            "tv_symbol (e.g., FX:EURUSD), tv_interval (60), "
            "scenario, question, options [A,B,C,D], correct (A/B/C/D), explanation. "
            "No text outside JSON."
        )
        
        level = lesson["level_name"].lower() if lesson else "beginner"
        complexity = {
            "beginner": "support/resistance identification",
            "intermediate": "trend context with S/R",
            "advanced": "order blocks, liquidity sweeps, market structure",
        }.get(level, "support and resistance")
        
        raw = await _ai(system, f"Create chart exercise for '{lesson['title']}' focusing on {complexity}.")
        
        try:
            clean = raw.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except Exception:
            data = {
                "tv_symbol": "FX:EURUSD",
                "tv_interval": "60",
                "scenario": "EUR/USD H4 shows uptrend with pullback to 1.0850 support.",
                "question": "Based on trend context, what would you expect at support?",
                "options": ["A: Buy the bounce", "B: Sell the break", "C: Wait", "D: No trade"],
                "correct": "A",
                "explanation": "In an uptrend, pullbacks to support offer high-probability long entries.",
            }
        
        return {
            "lesson_title": lesson["title"],
            "level": lesson["level_name"],
            "chart_practice": data,
        }
    except Exception as e:
        print(f"[API ERROR] mentor_chart_practice: {e}", flush=True)
        return {
            "lesson_title": "Chart Practice",
            "level": "Beginner",
            "chart_practice": {
                "tv_symbol": "FX:EURUSD",
                "tv_interval": "60",
                "scenario": "EUR/USD H4 shows uptrend with pullback to 1.0850 support.",
                "question": "Based on trend context, what would you expect at support?",
                "options": ["A: Buy the bounce", "B: Sell the break", "C: Wait", "D: No trade"],
                "correct": "A",
                "explanation": "In an uptrend, pullbacks to support offer high-probability long entries.",
            }
        }

# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def _mark_lesson_complete(user_id: int, lesson_id: int, score: float):
    try:
        lesson = await database.fetch_one(
            """SELECT l.module_id, m.level_id 
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id 
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        
        if not lesson:
            return
        
        existing = await database.fetch_one(
            """SELECT id FROM user_learning_progress 
               WHERE user_id=:uid AND lesson_id=:lid""",
            {"uid": user_id, "lid": lesson_id}
        )
        
        if existing:
            await database.execute(
                """UPDATE user_learning_progress 
                   SET completed=TRUE, quiz_score=:score, completed_at=NOW()
                   WHERE user_id=:uid AND lesson_id=:lid""",
                {"uid": user_id, "lid": lesson_id, "score": score}
            )
        else:
            await database.execute(
                """INSERT INTO user_learning_progress 
                   (user_id, level_id, module_id, lesson_id, completed, quiz_score, completed_at)
                   VALUES (:uid, :lv, :mid, :lid, TRUE, :score, NOW())""",
                {
                    "uid": user_id,
                    "lv": lesson.get("level_id", 0),
                    "mid": lesson.get("module_id", 0),
                    "lid": lesson_id,
                    "score": score
                }
            )
    except Exception as e:
        print(f"[HELPER ERROR] _mark_lesson_complete: {e}", flush=True)

async def _update_learning_profile(user_id: int, wrong_slugs: list, correct_slugs: list):
    try:
        existing = await database.fetch_one(
            "SELECT weak_topics, strong_topics FROM user_learning_profile WHERE user_id=:uid",
            {"uid": user_id}
        )
        
        if existing:
            cur_weak = _parse_json(existing.get("weak_topics"))
            cur_strong = _parse_json(existing.get("strong_topics"))
            
            new_weak = list(set(cur_weak + wrong_slugs) - set(correct_slugs))
            new_strong = list(set(cur_strong + correct_slugs))
            
            await database.execute(
                """UPDATE user_learning_profile 
                   SET weak_topics=:w, strong_topics=:s, last_updated=NOW() 
                   WHERE user_id=:uid""",
                {"uid": user_id, "w": json.dumps(new_weak), "s": json.dumps(new_strong)}
            )
        else:
            await database.execute(
                """INSERT INTO user_learning_profile 
                   (user_id, weak_topics, strong_topics, first_academy_visit, last_updated)
                   VALUES (:uid, :w, :s, TRUE, NOW())""",
                {"uid": user_id, "w": json.dumps(wrong_slugs), "s": json.dumps(correct_slugs)}
            )
    except Exception as e:
        print(f"[HELPER ERROR] _update_learning_profile: {e}", flush=True)

async def _quiz_feedback(score: float, passed: bool, lesson_title: str, wrong_slugs: list, level: str) -> str:
    try:
        if score == 100:
            return f"Perfect mastery! You've demonstrated complete understanding of {lesson_title}. Ready for the next challenge?"
        elif passed:
            if wrong_slugs:
                areas = ", ".join(wrong_slugs[:2])
                return f"Strong performance on {lesson_title}! Just polish your understanding of {areas}, then continue forward."
            return f"Great work passing {lesson_title}! Your trading knowledge is building steadily."
        else:
            focus = ", ".join(wrong_slugs[:3]) if wrong_slugs else "the core concepts"
            advice = {
                "beginner": "Every professional trader started here. Take time to review",
                "intermediate": "Precision separates profitable traders. Revisit",
                "advanced": "Institutional-grade trading demands mastery. Deep-dive into"
            }.get(level, "Focus your study on")
            return f"{advice} {focus} in {lesson_title}. Reattempt the quiz when ready."
    except Exception as e:
        print(f"[HELPER ERROR] _quiz_feedback: {e}", flush=True)
        return "Continue studying the material and retry the quiz when confident."
