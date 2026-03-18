"""
Pipways Trading Academy — Learning Router v3.0 (PATCHED)
Changes:
- Added badge awarding system (user_badges)
- Added first_academy_visit tracking
- Enhanced /mentor/guide to distinguish first visit vs Trading Coach mode
- Added /badges endpoints
- Added TradingView chart data endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json, os, httpx

from .security import get_current_user, get_user_id as _user_id
from .database import database

router = APIRouter()

OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL    = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════════════════════

class QuizAnswer(BaseModel):
    question_id: int
    selected_answer: str

class QuizSubmission(BaseModel):
    lesson_id: int
    answers: List[QuizAnswer]

class LessonCompleteRequest(BaseModel):
    lesson_id: int
    quiz_score: float = 0.0

class ProfileUpdateRequest(BaseModel):
    weak_topics:   List[str] = []
    strong_topics: List[str] = []


# ══════════════════════════════════════════════════════════════════════════════
# LLM HELPER
# ══════════════════════════════════════════════════════════════════════════════

async def _ai(system: str, user_msg: str, max_tokens: int = 600) -> str:
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
                        {"role": "user",   "content": user_msg},
                    ],
                }
            )
            data = res.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[TRADING COACH AI] Error: {e}", flush=True)
        return "I'm having trouble connecting right now. Please try again shortly."


# ══════════════════════════════════════════════════════════════════════════════
# BADGE SYSTEM HELPERS
# ══════════════════════════════════════════════════════════════════════════════

BADGE_DEFINITIONS = {
    "beginner_trader": {"name": "Beginner Trader", "icon": "fa-seedling", "color": "#34d399"},
    "technical_analyst": {"name": "Technical Analyst", "icon": "fa-chart-line", "color": "#60a5fa"},
    "strategy_builder": {"name": "Strategy Builder", "icon": "fa-chess-knight", "color": "#a78bfa"},
    "pipways_certified": {"name": "Pipways Certified Trader", "icon": "fa-certificate", "color": "#f59e0b"},
    "quiz_master": {"name": "Quiz Master", "icon": "fa-brain", "color": "#f472b6"},
    "perfect_score": {"name": "Perfect Score", "icon": "fa-star", "color": "#fbbf24"},
    "risk_manager": {"name": "Risk Manager", "icon": "fa-shield-alt", "color": "#22d3ee"},
    "psychology_pro": {"name": "Psychology Pro", "icon": "fa-brain", "color": "#e879f9"},
}

async def _award_badge(user_id: int, badge_type: str) -> bool:
    """Award a badge if not already earned. Returns True if newly awarded."""
    if badge_type not in BADGE_DEFINITIONS:
        return False
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

async def _check_and_award_badges(user_id: int, lesson_id: int = None, quiz_score: float = None):
    """Check progress and award appropriate badges."""
    newly_awarded = []
    
    # Count completed lessons per level
    level_counts = await database.fetch_all(
        "SELECT m.level_id, COUNT(*) as cnt "
        "FROM user_learning_progress p "
        "JOIN learning_lessons l ON l.id=p.lesson_id "
        "JOIN learning_modules m ON m.id=l.module_id "
        "WHERE p.user_id=:uid AND p.completed=TRUE "
        "GROUP BY m.level_id",
        {"uid": user_id}
    )
    level_totals = await database.fetch_all(
        "SELECT level_id, COUNT(*) as total FROM learning_modules m "
        "JOIN learning_lessons l ON l.module_id=m.id "
        "GROUP BY level_id"
    )
    level_map = {r["level_id"]: r["cnt"] for r in level_counts}
    total_map = {r["level_id"]: r["total"] for r in level_totals}
    
    # Beginner completion (level 1)
    if level_map.get(1, 0) >= total_map.get(1, 999):
        if await _award_badge(user_id, "beginner_trader"):
            newly_awarded.append("beginner_trader")
    
    # Intermediate completion (level 2)
    if level_map.get(2, 0) >= total_map.get(2, 999):
        if await _award_badge(user_id, "technical_analyst"):
            newly_awarded.append("technical_analyst")
    
    # Advanced completion (level 3)
    if level_map.get(3, 0) >= total_map.get(3, 999):
        if await _award_badge(user_id, "strategy_builder"):
            newly_awarded.append("strategy_builder")
        # Check for full certification (all levels)
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
        # Count high scores (80%+)
        high_scores = await database.fetch_val(
            "SELECT COUNT(*) FROM user_learning_progress WHERE user_id=:uid AND quiz_score>=80",
            {"uid": user_id}
        )
        if high_scores and int(high_scores) >= 10:
            if await _award_badge(user_id, "quiz_master"):
                newly_awarded.append("quiz_master")
    
    # Topic-specific badges
    if lesson_id:
        lesson = await database.fetch_one(
            "SELECT m.title FROM learning_lessons l "
            "JOIN learning_modules m ON m.id=l.module_id WHERE l.id=:lid",
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
    
    return newly_awarded


# ══════════════════════════════════════════════════════════════════════════════
# READ ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/levels")
async def get_levels(current_user=Depends(get_current_user)):
    rows = await database.fetch_all(
        "SELECT id, name, description, order_index FROM learning_levels ORDER BY order_index"
    )
    return [dict(r) for r in rows]


@router.get("/modules/{level_id}")
async def get_modules(level_id: int, current_user=Depends(get_current_user)):
    level = await database.fetch_one("SELECT id FROM learning_levels WHERE id=:lid", {"lid": level_id})
    if not level:
        raise HTTPException(404, "Level not found")

    modules = await database.fetch_all(
        "SELECT id,title,description,order_index FROM learning_modules "
        "WHERE level_id=:lid ORDER BY order_index",
        {"lid": level_id}
    )
    user_id = _user_id(current_user)
    result = []
    for m in modules:
        total = await database.fetch_val(
            "SELECT COUNT(*) FROM learning_lessons WHERE module_id=:mid", {"mid": m["id"]}
        )
        done = await database.fetch_val(
            "SELECT COUNT(*) FROM user_learning_progress "
            "WHERE user_id=:uid AND module_id=:mid AND completed=TRUE",
            {"uid": user_id, "mid": m["id"]}
        )
        result.append({
            **dict(m),
            "lesson_count":    total,
            "completed_count": done,
            "is_complete":     total > 0 and done >= total,
        })
    return result


@router.get("/lessons/{module_id}")
async def get_lessons(module_id: int, current_user=Depends(get_current_user)):
    module = await database.fetch_one("SELECT id FROM learning_modules WHERE id=:mid", {"mid": module_id})
    if not module:
        raise HTTPException(404, "Module not found")

    lessons = await database.fetch_all(
        "SELECT id,title,order_index FROM learning_lessons WHERE module_id=:mid ORDER BY order_index",
        {"mid": module_id}
    )
    user_id = _user_id(current_user)
    result = []
    for i, les in enumerate(lessons):
        progress = await database.fetch_one(
            "SELECT completed, quiz_score FROM user_learning_progress "
            "WHERE user_id=:uid AND lesson_id=:lid",
            {"uid": user_id, "lid": les["id"]}
        )
        unlocked = (i == 0)
        if i > 0:
            prev_id  = lessons[i - 1]["id"]
            prev_row = await database.fetch_one(
                "SELECT completed FROM user_learning_progress WHERE user_id=:uid AND lesson_id=:lid",
                {"uid": user_id, "lid": prev_id}
            )
            unlocked = prev_row is not None and bool(prev_row["completed"])

        result.append({
            **dict(les),
            "completed":  bool(progress["completed"]) if progress else False,
            "quiz_score": progress["quiz_score"]      if progress else None,
            "unlocked":   unlocked,
        })
    return result


@router.get("/lesson/{lesson_id}")
async def get_lesson(lesson_id: int, current_user=Depends(get_current_user)):
    lesson = await database.fetch_one(
        "SELECT l.id, l.title, l.content, l.order_index, l.module_id, "
        "       m.title AS module_title, m.level_id, lv.name AS level_name "
        "FROM   learning_lessons l "
        "JOIN   learning_modules m  ON m.id = l.module_id "
        "JOIN   learning_levels  lv ON lv.id = m.level_id "
        "WHERE  l.id = :lid",
        {"lid": lesson_id}
    )
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    
    # Get adjacent lessons for navigation
    user_id = _user_id(current_user)
    adj = await database.fetch_all(
        "SELECT l.id, l.title, l.order_index, "
        "EXISTS(SELECT 1 FROM user_learning_progress p WHERE p.lesson_id=l.id AND p.user_id=:uid AND p.completed=TRUE) as completed "
        "FROM learning_lessons l "
        "WHERE l.module_id = (SELECT module_id FROM learning_lessons WHERE id=:lid) "
        "ORDER BY l.order_index",
        {"lid": lesson_id, "uid": user_id}
    )
    current_idx = next((i for i, a in enumerate(adj) if a["id"] == lesson_id), -1)
    prev_lesson = adj[current_idx - 1] if current_idx > 0 else None
    next_lesson = adj[current_idx + 1] if current_idx < len(adj) - 1 else None
    
    result = dict(lesson)
    result["prev_lesson"] = {"id": prev_lesson["id"], "title": prev_lesson["title"], "completed": prev_lesson["completed"]} if prev_lesson else None
    result["next_lesson"] = {"id": next_lesson["id"], "title": next_lesson["title"], "completed": next_lesson["completed"]} if next_lesson else None
    return result


@router.get("/quiz/{lesson_id}")
async def get_quiz(lesson_id: int, current_user=Depends(get_current_user)):
    """Return quiz questions — correct_answer is NEVER sent to the client."""
    lesson = await database.fetch_one("SELECT id FROM learning_lessons WHERE id=:lid", {"lid": lesson_id})
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    questions = await database.fetch_all(
        "SELECT id, question, option_a, option_b, option_c, option_d "
        "FROM lesson_quizzes WHERE lesson_id=:lid ORDER BY id",
        {"lid": lesson_id}
    )
    return {"lesson_id": lesson_id, "question_count": len(questions), "questions": [dict(q) for q in questions]}


@router.get("/progress/{user_id}")
async def get_progress(user_id: int, current_user=Depends(get_current_user)):
    caller = _user_id(current_user)
    if caller != user_id and not current_user.get("is_admin"):
        raise HTTPException(403, "Forbidden")

    rows = await database.fetch_all(
        "SELECT p.id, p.level_id, p.module_id, p.lesson_id, p.completed, "
        "       p.quiz_score, p.completed_at, l.title AS lesson_title, m.title AS module_title "
        "FROM   user_learning_progress p "
        "LEFT JOIN learning_lessons l ON l.id = p.lesson_id "
        "LEFT JOIN learning_modules m ON m.id = p.module_id "
        "WHERE  p.user_id = :uid",
        {"uid": user_id}
    )
    levels = await database.fetch_all(
        "SELECT id, name FROM learning_levels ORDER BY order_index"
    )
    summary = []
    for lv in levels:
        total = await database.fetch_val(
            "SELECT COUNT(*) FROM learning_lessons les "
            "JOIN learning_modules m ON m.id=les.module_id WHERE m.level_id=:lid",
            {"lid": lv["id"]}
        )
        done = await database.fetch_val(
            "SELECT COUNT(*) FROM user_learning_progress "
            "WHERE user_id=:uid AND level_id=:lid AND completed=TRUE",
            {"uid": user_id, "lid": lv["id"]}
        )
        summary.append({
            "level_id":   lv["id"],
            "level_name": lv["name"],
            "total":      total,
            "completed":  done,
            "percent":    round((done / total * 100) if total else 0, 1),
        })
    return {"progress": [dict(r) for r in rows], "summary": summary}


@router.get("/profile/{user_id}")
async def get_profile(user_id: int, current_user=Depends(get_current_user)):
    caller = _user_id(current_user)
    if caller != user_id and not current_user.get("is_admin"):
        raise HTTPException(403, "Forbidden")

    row = await database.fetch_one(
        "SELECT weak_topics, strong_topics, first_academy_visit, last_updated "
        "FROM user_learning_profile WHERE user_id=:uid",
        {"uid": user_id}
    )
    if not row:
        return {"user_id": user_id, "weak_topics": [], "strong_topics": [], "first_academy_visit": True, "last_updated": None}
    return {
        "user_id":       user_id,
        "weak_topics":   _parse_json(row["weak_topics"]),
        "strong_topics": _parse_json(row["strong_topics"]),
        "first_academy_visit": row["first_academy_visit"] if row["first_academy_visit"] is not None else True,
        "last_updated":  row["last_updated"],
    }


@router.get("/badges/{user_id}")
async def get_badges(user_id: int, current_user=Depends(get_current_user)):
    """Get all earned badges for a user."""
    caller = _user_id(current_user)
    if caller != user_id and not current_user.get("is_admin"):
        raise HTTPException(403, "Forbidden")
    
    rows = await database.fetch_all(
        "SELECT badge_type, earned_at FROM user_badges WHERE user_id=:uid ORDER BY earned_at DESC",
        {"uid": user_id}
    )
    badges = []
    for r in rows:
        defn = BADGE_DEFINITIONS.get(r["badge_type"], {})
        badges.append({
            "type": r["badge_type"],
            "name": defn.get("name", r["badge_type"]),
            "icon": defn.get("icon", "fa-medal"),
            "color": defn.get("color", "#a78bfa"),
            "earned_at": r["earned_at"]
        })
    return {"user_id": user_id, "badges": badges, "count": len(badges)}


@router.post("/badges/check")
async def check_badges(current_user=Depends(get_current_user)):
    """Manually trigger badge check (returns newly awarded badges)."""
    user_id = _user_id(current_user)
    new_badges = await _check_and_award_badges(user_id)
    return {"newly_awarded": new_badges, "count": len(new_badges)}


# ══════════════════════════════════════════════════════════════════════════════
# WRITE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmission, current_user=Depends(get_current_user)):
    """
    Grade quiz server-side. Correct answers never leave the backend.
    - Updates user_quiz_results
    - Marks lesson complete if score ≥ 70
    - Updates user_learning_profile with weak topic_slugs
    - Awards badges
    - Returns AI Trading Coach feedback
    """
    user_id = _user_id(current_user)

    questions = await database.fetch_all(
        "SELECT id, correct_answer, explanation, topic_slug FROM lesson_quizzes "
        "WHERE lesson_id=:lid ORDER BY id",
        {"lid": payload.lesson_id}
    )
    if not questions:
        raise HTTPException(404, "No quiz questions found for this lesson")

    q_map   = {q["id"]: q for q in questions}
    total   = len(questions)
    correct = 0
    results = []
    wrong_slugs:  list[str] = []
    correct_slugs: list[str] = []

    for ans in payload.answers:
        q_id     = ans.question_id
        selected = ans.selected_answer.upper()
        row      = q_map.get(q_id)
        if not row:
            continue

        is_correct = (selected == row["correct_answer"].upper())
        if is_correct:
            correct += 1
            correct_slugs.append(row["topic_slug"])
        else:
            wrong_slugs.append(row["topic_slug"])

        await database.execute(
            "INSERT INTO user_quiz_results "
            "(user_id, lesson_id, question_id, selected_answer, is_correct, answered_at) "
            "VALUES (:uid, :lid, :qid, :ans, :ok, NOW())",
            {"uid": user_id, "lid": payload.lesson_id,
             "qid": q_id,   "ans": selected, "ok": is_correct}
        )
        results.append({
            "question_id":    q_id,
            "is_correct":     is_correct,
            "correct_answer": row["correct_answer"],
            "explanation":    row["explanation"],
        })

    score  = round((correct / total * 100) if total else 0, 1)
    passed = score >= 70

    if passed:
        await _mark_lesson_complete(user_id, payload.lesson_id, score)

    # Adaptive engine: remove correct slugs from weak_topics, add wrong slugs
    await _update_learning_profile(user_id, wrong_slugs, correct_slugs)

    # Check badges (quiz_score sent for perfect score detection)
    new_badges = await _check_and_award_badges(user_id, payload.lesson_id, score)

    # Get lesson name for feedback
    lesson = await database.fetch_one(
        "SELECT l.title, lv.name AS level_name FROM learning_lessons l "
        "JOIN learning_modules m ON m.id=l.module_id "
        "JOIN learning_levels lv ON lv.id=m.level_id "
        "WHERE l.id=:lid",
        {"lid": payload.lesson_id}
    )
    feedback = await _quiz_feedback(
        score, passed,
        lesson["title"] if lesson else "this lesson",
        wrong_slugs,
        lesson["level_name"].lower() if lesson else "intermediate"
    )

    return {
        "score":           score,
        "correct":         correct,
        "total":           total,
        "passed":          passed,
        "results":         results,
        "mentor_feedback": feedback,
        "new_badges":      new_badges,
    }


@router.post("/lesson/complete")
async def complete_lesson(payload: LessonCompleteRequest, current_user=Depends(get_current_user)):
    user_id = _user_id(current_user)
    await _mark_lesson_complete(user_id, payload.lesson_id, payload.quiz_score)
    new_badges = await _check_and_award_badges(user_id, payload.lesson_id)
    return {"success": True, "new_badges": new_badges}


@router.post("/profile/update")
async def update_profile(payload: ProfileUpdateRequest, current_user=Depends(get_current_user)):
    user_id = _user_id(current_user)
    await _upsert_profile(user_id, json.dumps(payload.weak_topics), json.dumps(payload.strong_topics))
    return {"success": True}


@router.post("/profile/first-visit-complete")
async def mark_first_visit_complete(current_user=Depends(get_current_user)):
    """Mark that user has seen the Trading Academy welcome."""
    user_id = _user_id(current_user)
    await database.execute(
        "INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, first_academy_visit, last_updated) "
        "VALUES (:uid, '[]', '[]', FALSE, NOW()) "
        "ON CONFLICT (user_id) DO UPDATE SET first_academy_visit=FALSE, last_updated=NOW()",
        {"uid": user_id}
    )
    return {"success": True, "first_academy_visit": False}


# ══════════════════════════════════════════════════════════════════════════════
# AI TRADING COACH ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/mentor/guide/{user_id}")
async def mentor_guide(user_id: int, current_user=Depends(get_current_user)):
    """
    Pipways Trading Coach — Personalized guidance banner.
    First visit: Welcome message.
    Subsequent: Recommendation based on progress & weak topics.
    """
    caller = _user_id(current_user)
    if caller != user_id and not current_user.get("is_admin"):
        raise HTTPException(403, "Forbidden")

    profile = await database.fetch_one(
        "SELECT weak_topics, strong_topics, first_academy_visit FROM user_learning_profile WHERE user_id=:uid",
        {"uid": user_id}
    )
    is_first_visit = True
    if profile and profile["first_academy_visit"] is False:
        is_first_visit = False

    progress = await database.fetch_all(
        "SELECT p.lesson_id, p.completed, p.quiz_score, l.title "
        "FROM user_learning_progress p JOIN learning_lessons l ON l.id=p.lesson_id "
        "WHERE p.user_id=:uid",
        {"uid": user_id}
    )
    
    done   = [r["title"] for r in progress if r["completed"]]
    weak   = _parse_json(profile["weak_topics"]) if profile else []
    strong = _parse_json(profile["strong_topics"]) if profile else []

    # Find next recommended lesson
    next_lesson = await database.fetch_one(
        "SELECT l.id, l.title, m.title AS module_title, lv.name AS level_name "
        "FROM learning_lessons l "
        "JOIN learning_modules m ON m.id=l.module_id "
        "JOIN learning_levels lv ON lv.id=m.level_id "
        "WHERE l.id NOT IN ("
        "  SELECT lesson_id FROM user_learning_progress WHERE user_id=:uid AND completed=TRUE"
        ") ORDER BY m.order_index, l.order_index LIMIT 1",
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
        f"Weak topics to reinforce: {', '.join(weak) if weak else 'none'}. "
        f"Strong topics: {', '.join(strong) if strong else 'none'}. "
        f"Next lesson queued: {next_lesson['title'] + ' in ' + next_lesson['module_title'] if next_lesson else 'Academy complete'}."
    )
    system = (
        "You are the Pipways Trading Coach. Give a motivational 2-sentence coaching message. "
        "Acknowledge their progress, mention one weak area to focus on, and encourage them to complete the next specific lesson listed. "
        "Be warm, professional, and end with 'Continue Learning' energy."
    )
    message = await _ai(system, f"Student progress context:\n{ctx}")

    return {
        "type": "recommendation",
        "message": message,
        "next_lesson": dict(next_lesson) if next_lesson else None,
        "first_visit": False,
        "completed_count": len(done),
        "weak_topics": weak,
    }


@router.post("/mentor/teach")
async def mentor_teach(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    """
    Pipways Trading Coach — Explains lesson concepts, answers questions, gives examples.
    This is the teaching mode (distinct from Global AI Mentor).
    """
    user_id = _user_id(current_user)
    lesson  = await database.fetch_one(
        "SELECT l.title, l.content, m.title AS module_title, lv.name AS level_name "
        "FROM learning_lessons l "
        "JOIN learning_modules m  ON m.id=l.module_id "
        "JOIN learning_levels  lv ON lv.id=m.level_id "
        "WHERE l.id=:lid",
        {"lid": lesson_id}
    )
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    profile  = await database.fetch_one(
        "SELECT weak_topics FROM user_learning_profile WHERE user_id=:uid", {"uid": user_id}
    )
    weak = _parse_json(profile["weak_topics"]) if profile else []
    level = lesson["level_name"].lower()

    tone = {
        "beginner":     "Use very simple language and real-world analogies. Avoid jargon entirely. Be encouraging.",
        "intermediate": "Use technical terms with clear definitions. Connect concepts to chart examples.",
        "advanced":     "Use institutional terminology. Discuss market structure, liquidity and order flow.",
    }.get(level, "Use clear, professional language.")

    system = (
        "You are the Pipways Trading Coach. "
        f"Teaching style: {tone} "
        "Structure your explanation as: "
        "1) Warm opening (1 sentence). "
        "2) Core concept — one clear sentence. "
        "3) Step-by-step breakdown (numbered). "
        "4) Trade example (pair, entry, stop, target). "
        "5) One common pitfall. "
        "6) Quick summary (1 sentence). "
        "Keep response under 450 words. Do not recommend other lessons — only explain THIS lesson content."
    )
    user_msg = (
        f"Explain this lesson in detail: {lesson['title']} ({lesson['module_title']})\n\n"
        f"Reference content:\n{lesson['content'][:1200]}\n\n"
        f"Student's weak topics to reinforce during explanation: {', '.join(weak) if weak else 'none'}."
    )

    explanation = await _ai(system, user_msg)

    return {
        "lesson_title":  lesson["title"],
        "module_title":  lesson["module_title"],
        "level":         lesson["level_name"],
        "explanation":   explanation,
        "coach_type":    "Trading Coach",
    }


@router.post("/mentor/practice")
async def mentor_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    """Trading Coach generates a unique practice scenario exercise."""
    lesson = await database.fetch_one(
        "SELECT l.title, l.content, lv.name AS level_name "
        "FROM learning_lessons l "
        "JOIN learning_modules m ON m.id=l.module_id "
        "JOIN learning_levels lv ON lv.id=m.level_id "
        "WHERE l.id=:lid",
        {"lid": lesson_id}
    )
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    system = (
        "You are a Pipways Trading Coach. Create ONE short, realistic practice exercise. "
        "Format: Scenario (1–2 sentences) → Question → blank line → Model Answer. "
        "Use different currency pairs and price levels each time. Under 180 words."
    )
    exercise = await _ai(
        system,
        f"Create a practice exercise for '{lesson['title']}' at {lesson['level_name']} level.\n"
        f"Context: {lesson['content'][:600]}"
    )

    return {"lesson_title": lesson["title"], "exercise": exercise}


@router.post("/mentor/chart-practice")
async def mentor_chart_practice(
    lesson_id: int = Query(...),
    current_user=Depends(get_current_user)
):
    """
    Chart-based practice exercise with TradingView integration.
    """
    lesson = await database.fetch_one(
        "SELECT l.title, lv.name AS level_name "
        "FROM learning_lessons l "
        "JOIN learning_modules m ON m.id=l.module_id "
        "JOIN learning_levels lv ON lv.id=m.level_id "
        "WHERE l.id=:lid",
        {"lid": lesson_id}
    )
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    system = (
        "You are a trading mentor creating a chart-reading exercise. "
        "Format your response as valid JSON with EXACTLY these keys: "
        '{"tv_symbol":"FX:EURUSD","tv_interval":"240","scenario":"...","question":"...","options":["A: ...","B: ...","C: ...","D: ..."],'
        '"correct":"A","explanation":"..."}. '
        "tv_symbol must be TradingView format like FX:EURUSD, OANDA:GBPUSD. "
        "tv_interval: 1,5,15,30,60,240,D,W. "
        "Vary the currency pair each call. No text outside JSON."
    )
    level = lesson["level_name"].lower()
    complexity = {
        "beginner":     "basic support/resistance identification",
        "intermediate": "trend context with support/resistance",
        "advanced":     "order blocks, liquidity sweeps, market structure",
    }.get(level, "support and resistance")

    raw = await _ai(system, f"Create chart exercise for '{lesson['title']}' focusing on {complexity}.")

    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        data  = json.loads(clean)
    except Exception:
        data = {
            "tv_symbol":    "FX:EURUSD",
            "tv_interval":  "240",
            "scenario":     "EUR/USD H4 chart. Price has been in an uptrend forming higher highs and higher lows, and is now pulling back to a key support level at 1.0850.",
            "question":     "Based on the uptrend context, what would you expect at the 1.0850 support?",
            "options":      ["A: Buy the bounce (trend continuation)", "B: Sell into the pullback", "C: Wait for more confirmation", "D: No trade — trend is unclear"],
            "correct":      "A",
            "explanation":  "In an uptrend, pullbacks to support offer high-probability long entries with the trend. The uptrend structure (HH+HL) is still intact.",
        }

    return {
        "lesson_title": lesson["title"],
        "level":        lesson["level_name"],
        "chart_practice": data,
    }


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_json(value) -> list:
    if value is None: return []
    if isinstance(value, list): return value
    try: return json.loads(value)
    except Exception: return []


async def _mark_lesson_complete(user_id: int, lesson_id: int, score: float) -> None:
    lesson = await database.fetch_one(
        "SELECT l.module_id, m.level_id FROM learning_lessons l "
        "JOIN learning_modules m ON m.id=l.module_id WHERE l.id=:lid",
        {"lid": lesson_id}
    )
    if not lesson:
        return

    existing = await database.fetch_one(
        "SELECT id FROM user_learning_progress WHERE user_id=:uid AND lesson_id=:lid",
        {"uid": user_id, "lid": lesson_id}
    )
    if existing:
        await database.execute(
            "UPDATE user_learning_progress "
            "SET completed=TRUE, quiz_score=:score, completed_at=NOW() "
            "WHERE user_id=:uid AND lesson_id=:lid",
            {"uid": user_id, "lid": lesson_id, "score": score}
        )
    else:
        await database.execute(
            "INSERT INTO user_learning_progress "
            "(user_id, level_id, module_id, lesson_id, completed, quiz_score, completed_at) "
            "VALUES (:uid, :lv, :mid, :lid, TRUE, :score, NOW())",
            {"uid": user_id, "lv": lesson["level_id"],
             "mid": lesson["module_id"], "lid": lesson_id, "score": score}
        )


async def _update_learning_profile(user_id: int, wrong_slugs: list, correct_slugs: list) -> None:
    """
    Add wrong topic_slugs to weak_topics.
    Remove correct topic_slugs from weak_topics (mastered).
    Add correct topic_slugs to strong_topics.
    """
    existing = await database.fetch_one(
        "SELECT weak_topics, strong_topics FROM user_learning_profile WHERE user_id=:uid",
        {"uid": user_id}
    )
    if existing:
        cur_weak   = _parse_json(existing["weak_topics"])
        cur_strong = _parse_json(existing["strong_topics"])
        new_weak   = list(set(cur_weak + wrong_slugs) - set(correct_slugs))
        new_strong = list(set(cur_strong + correct_slugs))
        await database.execute(
            "UPDATE user_learning_profile "
            "SET weak_topics=:w, strong_topics=:s, last_updated=NOW() WHERE user_id=:uid",
            {"uid": user_id, "w": json.dumps(new_weak), "s": json.dumps(new_strong)}
        )
    else:
        await database.execute(
            "INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, first_academy_visit, last_updated) "
            "VALUES (:uid, :w, :s, TRUE, NOW())",
            {"uid": user_id,
             "w": json.dumps(list(set(wrong_slugs))),
             "s": json.dumps(list(set(correct_slugs)))}
        )


async def _upsert_profile(user_id: int, weak_json: str, strong_json: str) -> None:
    existing = await database.fetch_one(
        "SELECT id FROM user_learning_profile WHERE user_id=:uid", {"uid": user_id}
    )
    if existing:
        await database.execute(
            "UPDATE user_learning_profile SET weak_topics=:w, strong_topics=:s, last_updated=NOW() "
            "WHERE user_id=:uid",
            {"uid": user_id, "w": weak_json, "s": strong_json}
        )
    else:
        await database.execute(
            "INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, first_academy_visit, last_updated) "
            "VALUES (:uid, :w, :s, TRUE, NOW())",
            {"uid": user_id, "w": weak_json, "s": strong_json}
        )


async def _quiz_feedback(
    score: float, passed: bool, lesson_title: str,
    wrong_slugs: list, level: str
) -> str:
    if not OPENROUTER_API_KEY:
        if passed:
            return f"Excellent! You scored {score}% and completed '{lesson_title}'."
        return f"You scored {score}%. You need 70% to pass. Review the lesson and try again — you can do it!"

    tone = {
        "beginner":     "Be very encouraging and gentle. Use simple language.",
        "intermediate": "Be professional and direct. Reference specific concepts.",
        "advanced":     "Be concise and analytical.",
    }.get(level, "Be encouraging.")

    slugs = ", ".join(set(wrong_slugs)) if wrong_slugs else "none"
    status = "passed" if passed else f"did not pass (needs 70%, scored {score}%)"

    system = (
        f"You are the Pipways Trading Coach. {tone} "
        "Write 2–3 sentences of quiz feedback. End with a specific action."
    )
    return await _ai(
        system,
        f"Student scored {score}% on '{lesson_title}' and {status}. "
        f"Topics with wrong answers: {slugs}."
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN / DIAGNOSTIC ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/health")
async def lms_health():
    """
    Public health check — no auth required.
    Returns table existence and row counts so you can diagnose setup issues.
    """
    result = {}
    tables = [
        "learning_levels", "learning_modules", "learning_lessons",
        "lesson_quizzes", "user_learning_progress",
        "user_quiz_results", "user_learning_profile", "user_badges"
    ]
    for t in tables:
        try:
            n = await database.fetch_val(f"SELECT COUNT(*) FROM {t}")
            result[t] = int(n)
        except Exception as e:
            result[t] = f"ERROR: {e}"
    return {
        "status": "ok" if result.get("learning_levels", 0) > 0 else "no_curriculum",
        "tables": result,
        "curriculum_valid": result.get("learning_levels", 0) == 3 and result.get("learning_modules", 0) >= 18,
        "tip": (
            "All tables present and curriculum seeded — ready to use."
            if result.get("learning_levels", 0) > 0
            else "Curriculum is empty. It will auto-seed on next init, or call POST /learning/admin/seed"
        )
    }


@router.post("/admin/seed")
async def admin_seed_curriculum(current_user=Depends(get_current_user)):
    """
    Admin-only endpoint to (re)seed the default curriculum.
    Safe to call multiple times — checks if levels already exist first.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(403, "Admin access required")

    try:
        from .lms_init import _seed_curriculum, init_lms_tables
        await init_lms_tables()
        count = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
        if count > 0:
            return {
                "status": "already_seeded",
                "levels": int(count),
                "message": "Curriculum already exists. Delete levels manually to re-seed."
            }
        await _seed_curriculum()
        final = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
        return {
            "status": "seeded",
            "levels": int(final),
            "message": f"Default curriculum seeded successfully — {final} levels created."
        }
    except Exception as e:
        raise HTTPException(500, f"Seed failed: {e}")
