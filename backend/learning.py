"""
Pipways Trading Academy — Learning Router v4.1 (Production - Defensive)
Features: Trading Coach AI, Badge System, 5-Question Quizzes, Progress Tracking
Includes: Comprehensive error handling to prevent HTTP 500 crashes
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
# LLM HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def _ai(system: str, user_msg: str, max_tokens: int = 800) -> str:
    if not OPENROUTER_API_KEY:
        return "AI Trading Coach is currently unavailable. Please configure OPENROUTER_API_KEY."
    try:
        async with httpx.AsyncClient(timeout=30) as client:
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
            data = res.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[TRADING COACH AI] Error: {e}", flush=True)
        return "I'm having trouble connecting right now. Please try again shortly."

# ═══════════════════════════════════════════════════════════════════════════════
# BADGE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

BADGE_DEFINITIONS = {
    "beginner_trader": {"name": "Beginner Trader", "icon": "fa-seedling", "color": "#34d399", "desc": "Completed Beginner level"},
    "technical_analyst": {"name": "Technical Analyst", "icon": "fa-chart-line", "color": "#60a5fa", "desc": "Completed Intermediate level"},
    "strategy_builder": {"name": "Strategy Builder", "icon": "fa-chess-knight", "color": "#a78bfa", "desc": "Completed Advanced level"},
    "pipways_certified": {"name": "Pipways Certified", "icon": "fa-certificate", "color": "#f59e0b", "desc": "Completed entire Academy curriculum"},
    "quiz_master": {"name": "Quiz Master", "icon": "fa-brain", "color": "#f472b6", "desc": "Passed 10 quizzes with 80%+"},
    "perfect_score": {"name": "Perfect Score", "icon": "fa-star", "color": "#fbbf24", "desc": "Scored 100% on any quiz"},
    "risk_manager": {"name": "Risk Manager", "icon": "fa-shield-alt", "color": "#22d3ee", "desc": "Mastered Risk Management modules"},
    "psychology_pro": {"name": "Psychology Pro", "icon": "fa-brain", "color": "#e879f9", "desc": "Completed Trading Psychology module"},
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
    newly_awarded = []
    
    try:
        # Level completion badges
        level_counts = await database.fetch_all(
            """SELECT m.level_id, COUNT(*) as cnt 
               FROM user_learning_progress p
               JOIN learning_lessons l ON l.id = p.lesson_id
               JOIN learning_modules m ON m.id = l.module_id
               WHERE p.user_id=:uid AND p.completed=TRUE
               GROUP BY m.level_id""",
            {"uid": user_id}
        )
        
        level_totals = await database.fetch_all(
            """SELECT level_id, COUNT(*) as total 
               FROM learning_modules m
               JOIN learning_lessons l ON l.module_id = m.id
               GROUP BY level_id""",
            {}
        )
        
        level_map = {r["level_id"]: r["cnt"] for r in level_counts} if level_counts else {}
        total_map = {r["level_id"]: r["total"] for r in level_totals} if level_totals else {}
        
        if level_map.get(1, 0) >= total_map.get(1, 999):
            if await _award_badge(user_id, "beginner_trader"):
                newly_awarded.append("beginner_trader")
        
        if level_map.get(2, 0) >= total_map.get(2, 999):
            if await _award_badge(user_id, "technical_analyst"):
                newly_awarded.append("technical_analyst")
        
        if level_map.get(3, 0) >= total_map.get(3, 999):
            if await _award_badge(user_id, "strategy_builder"):
                newly_awarded.append("strategy_builder")
            
            total_all = sum(total_map.values())
            done_all = sum(level_map.values())
            if done_all >= total_all:
                if await _award_badge(user_id, "pipways_certified"):
                    newly_awarded.append("pipways_certified")
        
        # Quiz badges
        if quiz_score is not None:
            if quiz_score == 100:
                if await _award_badge(user_id, "perfect_score"):
                    newly_awarded.append("perfect_score")
            
            try:
                high_scores = await database.fetch_val(
                    "SELECT COUNT(*) FROM user_learning_progress WHERE user_id=:uid AND quiz_score>=80",
                    {"uid": user_id}
                )
                if high_scores and int(high_scores) >= 10:
                    if await _award_badge(user_id, "quiz_master"):
                        newly_awarded.append("quiz_master")
            except Exception as e:
                print(f"[BADGE CHECK ERROR] Quiz master check failed: {e}", flush=True)
        
        # Topic badges
        if lesson_id:
            try:
                lesson = await database.fetch_one(
                    """SELECT m.title FROM learning_lessons l
                       JOIN learning_modules m ON m.id=l.module_id 
                       WHERE l.id=:lid""",
                    {"lid": lesson_id}
                )
                if lesson:
                    title = lesson["title"].lower()
                    if "risk" in title:
                        if await _award_badge(user_id, "risk_manager"):
                            newly_awarded.append("risk_manager")
                    if "psychology" in title:
                        if await _award_badge(user_id, "psychology_pro"):
                            newly_awarded.append("psychology_pro")
            except Exception as e:
                print(f"[BADGE CHECK ERROR] Topic badge check failed: {e}", flush=True)
    except Exception as e:
        print(f"[BADGE CHECK ERROR] General badge check failed: {e}", flush=True)
    
    return newly_awarded

# ═══════════════════════════════════════════════════════════════════════════════
# READ ENDPOINTS — All wrapped with try/except for safety
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
        return []  # Return empty array instead of crashing

@router.get("/modules/{level_id}")
async def get_modules(level_id: int, current_user=Depends(get_current_user)):
    try:
        level = await database.fetch_one("SELECT id FROM learning_levels WHERE id=:lid", {"lid": level_id})
        if not level:
            return []  # Return empty rather than 404
        
        modules = await database.fetch_all(
            """SELECT id, title, description, order_index 
               FROM learning_modules 
               WHERE level_id=:lid ORDER BY order_index""",
            {"lid": level_id}
        )
        
        if not modules:
            return []
        
        user_id = current_user.get("id") if current_user else 0
        result = []
        
        for m in modules:
            try:
                total = await database.fetch_val(
                    "SELECT COUNT(*) FROM learning_lessons WHERE module_id=:mid",
                    {"mid": m["id"]}
                ) or 0
                
                done = await database.fetch_val(
                    """SELECT COUNT(*) FROM user_learning_progress 
                       WHERE user_id=:uid AND module_id=:mid AND completed=TRUE""",
                    {"uid": user_id, "mid": m["id"]}
                ) or 0
                
                result.append({
                    **dict(m),
                    "lesson_count": int(total),
                    "completed_count": int(done),
                    "is_complete": total > 0 and done >= total,
                })
            except Exception as e:
                print(f"[API ERROR] get_modules loop: {e}", flush=True)
                result.append({**dict(m), "lesson_count": 0, "completed_count": 0, "is_complete": False})
        
        return result
    except Exception as e:
        print(f"[API ERROR] get_modules: {e}", flush=True)
        return []

@router.get("/lessons/{module_id}")
async def get_lessons(module_id: int, current_user=Depends(get_current_user)):
    try:
        module = await database.fetch_one("SELECT id FROM learning_modules WHERE id=:mid", {"mid": module_id})
        if not module:
            return []
        
        lessons = await database.fetch_all(
            """SELECT id, title, order_index 
               FROM learning_lessons 
               WHERE module_id=:mid ORDER BY order_index""",
            {"mid": module_id}
        )
        
        if not lessons:
            return []
        
        user_id = current_user.get("id") if current_user else 0
        result = []
        
        for i, les in enumerate(lessons):
            try:
                progress = await database.fetch_one(
                    """SELECT completed, quiz_score 
                       FROM user_learning_progress 
                       WHERE user_id=:uid AND lesson_id=:lid""",
                    {"uid": user_id, "lid": les["id"]}
                )
                
                unlocked = (i == 0)
                if i > 0 and lessons:
                    prev_id = lessons[i - 1]["id"]
                    prev_row = await database.fetch_one(
                        """SELECT completed FROM user_learning_progress 
                           WHERE user_id=:uid AND lesson_id=:lid""",
                        {"uid": user_id, "lid": prev_id}
                    )
                    unlocked = prev_row is not None and bool(prev_row["completed"])
                
                result.append({
                    **dict(les),
                    "completed": bool(progress["completed"]) if progress else False,
                    "quiz_score": progress["quiz_score"] if progress else None,
                    "unlocked": unlocked,
                })
            except Exception as e:
                print(f"[API ERROR] get_lessons loop: {e}", flush=True)
                result.append({**dict(les), "completed": False, "quiz_score": None, "unlocked": i == 0})
        
        return result
    except Exception as e:
        print(f"[API ERROR] get_lessons: {e}", flush=True)
        return []

@router.get("/lesson/{lesson_id}")
async def get_lesson(lesson_id: int, current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            """SELECT l.id, l.title, l.content, l.order_index, l.module_id,
                      m.title AS module_title, m.level_id, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id = l.module_id
               JOIN learning_levels lv ON lv.id = m.level_id
               WHERE l.id = :lid""",
            {"lid": lesson_id}
        )
        
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        
        user_id = current_user.get("id") if current_user else 0
        
        # Get adjacent lessons
        adj = await database.fetch_all(
            """SELECT l.id, l.title, l.order_index,
                      EXISTS(SELECT 1 FROM user_learning_progress p 
                             WHERE p.lesson_id=l.id AND p.user_id=:uid AND p.completed=TRUE) as completed
               FROM learning_lessons l
               WHERE l.module_id = (SELECT module_id FROM learning_lessons WHERE id=:lid)
               ORDER BY l.order_index""",
            {"lid": lesson_id, "uid": user_id}
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
        raise HTTPException(500, "Failed to load lesson data")

@router.get("/quiz/{lesson_id}")
async def get_quiz(lesson_id: int, current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one("SELECT id FROM learning_lessons WHERE id=:lid", {"lid": lesson_id})
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        
        questions = await database.fetch_all(
            """SELECT id, question, option_a, option_b, option_c, option_d
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
        caller = current_user.get("id") if current_user else 0
        is_admin = current_user.get("is_admin") if current_user else False
        
        if caller != user_id and not is_admin:
            # Return empty progress for unauthorized rather than 403
            return {
                "user_id": user_id,
                "total_lessons": 0,
                "completed_lessons": 0,
                "completion_rate": 0.0,
                "progress": [],
                "summary": []
            }
        
        rows = await database.fetch_all(
            """SELECT p.id, p.level_id, p.module_id, p.lesson_id, p.completed,
                      p.quiz_score, p.completed_at, l.title AS lesson_title, m.title AS module_title
               FROM user_learning_progress p
               LEFT JOIN learning_lessons l ON l.id = p.lesson_id
               LEFT JOIN learning_modules m ON m.id = p.module_id
               WHERE p.user_id = :uid""",
            {"uid": user_id}
        )
        
        levels = await database.fetch_all("SELECT id, name FROM learning_levels ORDER BY order_index") or []
        
        summary = []
        for lv in levels:
            try:
                total = await database.fetch_val(
                    """SELECT COUNT(*) FROM learning_lessons les
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
        
        total_lessons_rows = await database.fetch_all("SELECT id FROM learning_lessons") or []
        total_lessons = len(total_lessons_rows)
        completed_lessons = sum(1 for p in (rows or []) if p and p.get('completed'))
        
        return {
            "user_id": user_id,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "completion_rate": round((completed_lessons / total_lessons * 100) if total_lessons else 0, 1),
            "progress": [dict(r) for r in (rows or [])],
            "summary": summary
        }
    except Exception as e:
        print(f"[API ERROR] get_progress: {e}", flush=True)
        # Return safe default on any error
        return {
            "user_id": user_id,
            "total_lessons": 0,
            "completed_lessons": 0,
            "completion_rate": 0.0,
            "progress": [],
            "summary": [],
            "error": "Failed to load progress"
        }

@router.get("/profile/{user_id}")
async def get_profile(user_id: int, current_user=Depends(get_current_user)):
    try:
        caller = current_user.get("id") if current_user else 0
        is_admin = current_user.get("is_admin") if current_user else False
        
        if caller != user_id and not is_admin:
            return {"user_id": user_id, "weak_topics": [], "strong_topics": [], "first_academy_visit": True, "last_updated": None}
        
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
        
        def parse_json(val):
            if not val:
                return []
            try:
                return json.loads(val) if isinstance(val, str) else val
            except:
                return []
        
        return {
            "user_id": user_id,
            "weak_topics": parse_json(row.get("weak_topics")),
            "strong_topics": parse_json(row.get("strong_topics")),
            "first_academy_visit": row.get("first_academy_visit") if row.get("first_academy_visit") is not None else True,
            "last_updated": row.get("last_updated"),
        }
    except Exception as e:
        print(f"[API ERROR] get_profile: {e}", flush=True)
        return {
            "user_id": user_id,
            "weak_topics": [],
            "strong_topics": [],
            "first_academy_visit": True,
            "last_updated": None,
            "error": "Failed to load profile"
        }

@router.get("/badges/{user_id}")
async def get_badges(user_id: int, current_user=Depends(get_current_user)):
    try:
        caller = current_user.get("id") if current_user else 0
        is_admin = current_user.get("is_admin") if current_user else False
        
        if caller != user_id and not is_admin:
            return {"user_id": user_id, "badges": [], "count": 0}
        
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
    except Exception as e:
        print(f"[API ERROR] get_badges: {e}", flush=True)
        return {"user_id": user_id, "badges": [], "count": 0, "error": "Failed to load badges"}

@router.post("/badges/check")
async def check_badges(current_user=Depends(get_current_user)):
    try:
        user_id = current_user.get("id") if current_user else 0
        if not user_id:
            return {"newly_awarded": [], "count": 0}
        
        new_badges = await _check_and_award_badges(user_id)
        return {"newly_awarded": new_badges, "count": len(new_badges)}
    except Exception as e:
        print(f"[API ERROR] check_badges: {e}", flush=True)
        return {"newly_awarded": [], "count": 0}

# ═══════════════════════════════════════════════════════════════════════════════
# WRITE ENDPOINTS — Wrapped for safety
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmission, current_user=Depends(get_current_user)):
    try:
        user_id = current_user.get("id") if current_user else 0
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        
        questions = await database.fetch_all(
            """SELECT id, correct_answer, explanation, topic_slug 
               FROM lesson_quizzes WHERE lesson_id=:lid ORDER BY id""",
            {"lid": payload.lesson_id}
        )
        
        if not questions:
            raise HTTPException(404, "No quiz questions found for this lesson")
        
        q_map = {q["id"]: q for q in questions}
        total = len(questions)
        correct = 0
        results = []
        wrong_slugs = []
        correct_slugs = []
        
        for ans in payload.answers:
            try:
                q_id = ans.question_id
                selected = ans.selected_answer.upper()
                row = q_map.get(q_id)
                
                if not row:
                    continue
                
                is_correct = (selected == row["correct_answer"].upper())
                if is_correct:
                    correct += 1
                    correct_slugs.append(row["topic_slug"])
                else:
                    wrong_slugs.append(row["topic_slug"])
                
                await database.execute(
                    """INSERT INTO user_quiz_results 
                       (user_id, lesson_id, question_id, selected_answer, is_correct, answered_at)
                       VALUES (:uid, :lid, :qid, :ans, :ok, NOW())""",
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
        
        lesson = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name 
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": payload.lesson_id}
        )
        
        feedback = await _quiz_feedback(
            score, passed,
            lesson["title"] if lesson else "this lesson",
            wrong_slugs,
            lesson["level_name"].lower() if lesson else "intermediate"
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
        raise HTTPException(500, "Failed to submit quiz")

@router.post("/lesson/complete")
async def complete_lesson(payload: LessonCompleteRequest, current_user=Depends(get_current_user)):
    try:
        user_id = current_user.get("id") if current_user else 0
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        
        await _mark_lesson_complete(user_id, payload.lesson_id, payload.quiz_score)
        new_badges = await _check_and_award_badges(user_id, payload.lesson_id)
        return {"success": True, "new_badges": new_badges}
    except Exception as e:
        print(f"[API ERROR] complete_lesson: {e}", flush=True)
        raise HTTPException(500, "Failed to complete lesson")

@router.post("/profile/first-visit-complete")
async def mark_first_visit_complete(current_user=Depends(get_current_user)):
    try:
        user_id = current_user.get("id") if current_user else 0
        if not user_id:
            raise HTTPException(401, "Not authenticated")
        
        await database.execute(
            """INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, first_academy_visit, last_updated)
               VALUES (:uid, '[]', '[]', FALSE, NOW())
               ON CONFLICT (user_id) DO UPDATE SET first_academy_visit=FALSE, last_updated=NOW()""",
            {"uid": user_id}
        )
        
        return {"success": True, "first_academy_visit": False}
    except Exception as e:
        print(f"[API ERROR] mark_first_visit_complete: {e}", flush=True)
        raise HTTPException(500, "Failed to update profile")

# ═══════════════════════════════════════════════════════════════════════════════
# AI TRADING COACH ENDPOINTS — Wrapped for safety
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/mentor/guide/{user_id}")
async def mentor_guide(user_id: int, current_user=Depends(get_current_user)):
    try:
        caller = current_user.get("id") if current_user else 0
        is_admin = current_user.get("is_admin") if current_user else False
        
        if caller != user_id and not is_admin:
            # Return generic fallback for unauthorized
            return {
                "type": "welcome",
                "message": "Welcome to Pipways Trading Academy! Start your journey with the Beginner level.",
                "next_lesson": None,
                "first_visit": True,
                "weak_topics": [],
            }
        
        profile = await database.fetch_one(
            """SELECT weak_topics, strong_topics, first_academy_visit 
               FROM user_learning_profile WHERE user_id=:uid""",
            {"uid": user_id}
        )
        
        is_first_visit = True
        if profile and profile.get("first_academy_visit") is False:
            is_first_visit = False
        
        progress = await database.fetch_all(
            """SELECT p.lesson_id, p.completed, p.quiz_score, l.title
               FROM user_learning_progress p 
               JOIN learning_lessons l ON l.id=p.lesson_id
               WHERE p.user_id=:uid""",
            {"uid": user_id}
        )
        
        done = [r["title"] for r in (progress or []) if r and r.get("completed")]
        weak = json.loads(profile["weak_topics"]) if profile and profile.get("weak_topics") else []
        strong = json.loads(profile["strong_topics"]) if profile and profile.get("strong_topics") else []
        
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
        
        if is_first_visit:
            return {
                "type": "welcome",
                "message": "Welcome to Pipways Trading Academy! Start your journey with the Beginner level. Master the basics, then progress through structured modules designed by professional traders.",
                "next_lesson": dict(next_lesson) if next_lesson else None,
                "first_visit": True,
                "weak_topics": [],
            }
        
        # Trading Coach recommendation mode
        ctx = (
            f"Completed lessons ({len(done)}): {', '.join(done[-5:]) if done else 'none yet'}. "
            f"Weak topics: {', '.join(weak) if weak else 'none'}. "
            f"Strong topics: {', '.join(strong) if strong else 'none'}. "
            f"Next lesson: {next_lesson['title'] + ' in ' + next_lesson['module_title'] if next_lesson else 'Academy complete'}."
        )
        
        system = (
            "You are the Pipways Trading Coach. Give a motivational 2-sentence coaching message. "
            "Acknowledge progress, mention one weak area to focus on, and encourage completion of the next lesson. "
            "Be warm, professional, and end with 'Continue Learning' energy."
        )
        
        message = await _ai(system, f"Student progress:\n{ctx}")
        
        return {
            "type": "recommendation",
            "message": message,
            "next_lesson": dict(next_lesson) if next_lesson else None,
            "first_visit": False,
            "completed_count": len(done),
            "weak_topics": weak,
        }
    except Exception as e:
        print(f"[API ERROR] mentor_guide: {e}", flush=True)
        traceback.print_exc()
        # Return safe fallback
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
        user_id = current_user.get("id") if current_user else 0
        
        lesson = await database.fetch_one(
            """SELECT l.title, l.content, m.title AS module_title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        
        profile = await database.fetch_one(
            "SELECT weak_topics FROM user_learning_profile WHERE user_id=:uid",
            {"uid": user_id}
        )
        
        weak = json.loads(profile["weak_topics"]) if profile and profile.get("weak_topics") else []
        level = lesson["level_name"].lower() if lesson.get("level_name") else "intermediate"
        
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
        
        content_preview = lesson.get("content", "")[:1200] if lesson.get("content") else ""
        explanation = await _ai(system, f"Explain: {lesson.get('title', '')}\n\nContent: {content_preview}")
        
        return {
            "lesson_title": lesson.get("title", ""),
            "module_title": lesson.get("module_title", ""),
            "level": lesson.get("level_name", ""),
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
            "explanation": "Trading Coach explanation is temporarily unavailable. Please review the lesson content and try the quiz to reinforce your learning."
        }

@router.post("/mentor/practice")
async def mentor_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            """SELECT l.title, l.content, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        
        system = (
            "You are a Pipways Trading Coach. Create ONE short, realistic practice exercise. "
            "Format: Scenario (1-2 sentences) → Question → Model Answer. "
            "Use different currency pairs each time. Under 180 words."
        )
        
        exercise = await _ai(system, f"Create exercise for '{lesson.get('title', '')}' at {lesson.get('level_name', 'Beginner')} level.")
        
        return {"lesson_title": lesson.get("title", ""), "exercise": exercise}
    except Exception as e:
        print(f"[API ERROR] mentor_practice: {e}", flush=True)
        return {
            "lesson_title": "Practice",
            "exercise": "Practice Exercise:\n\nScenario: EUR/USD is testing a key support level at 1.0850 after a downtrend.\n\nQuestion: What factors should you check before deciding to buy at support?\n\nModel Answer: Check 1) Higher timeframe trend direction, 2) Presence of bullish candlestick patterns (pin bar, engulfing), 3) RSI for oversold conditions, 4) Volume confirmation on the bounce. Only enter if multiple factors align."
        }

@router.post("/mentor/chart-practice")
async def mentor_chart_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id=l.module_id
               JOIN learning_levels lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        
        system = (
            "Create a chart-reading exercise. Return valid JSON with keys: "
            "tv_symbol (e.g., FX:EURUSD, OANDA:GBPUSD), tv_interval (60), "
            "scenario, question, options [A,B,C,D], correct (A/B/C/D), explanation. "
            "No text outside JSON."
        )
        
        level = lesson.get("level_name", "Beginner").lower()
        complexity = {
            "beginner": "support/resistance identification",
            "intermediate": "trend context with S/R",
            "advanced": "order blocks, liquidity sweeps, market structure",
        }.get(level, "support and resistance")
        
        raw = await _ai(system, f"Create chart exercise for '{lesson.get('title', '')}' focusing on {complexity}.")
        
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
            "lesson_title": lesson.get("title", ""),
            "level": lesson.get("level_name", ""),
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

def _parse_json(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except:
        return []

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
    """Generate contextual AI feedback for quiz results"""
    try:
        if score == 100:
            return f"Perfect mastery! You've demonstrated complete understanding of {lesson_title}. Ready for the next challenge?"
        elif passed:
            if wrong_slugs:
                areas = ", ".join(wrong_slugs[:2])
                return f"Strong performance on {lesson_title}! Just polish your understanding of {areas}, then continue forward."
            return f"Great work passing {lesson_title}! Your trading knowledge is building steadily. Proceed to the next lesson with confidence."
        else:
            # Failed - provide targeted encouragement
            focus = ", ".join(wrong_slugs[:3]) if wrong_slugs else "the core concepts"
            advice = {
                "beginner": "Every professional trader started here. Take time to review",
                "intermediate": "Precision separates profitable traders. Revisit",
                "advanced": "Institutional-grade trading demands mastery. Deep-dive into"
            }.get(level, "Focus your study on")
            return f"{advice} {focus} in {lesson_title}. Reattempt the quiz when the concepts click."
    except Exception as e:
        print(f"[HELPER ERROR] _quiz_feedback: {e}", flush=True)
        return "Continue studying the material and retry the quiz when you feel confident."
