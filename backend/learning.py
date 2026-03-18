"""
Pipways Trading Academy — Learning Router v3.0 (learning.py)
Enhanced with AI Mentor, Trading Coach, Badges, and Navigation
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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


# ══════════════════════════════════════════════════════════════════════════════
# LLM HELPER
# ══════════════════════════════════════════════════════════════════════════════

async def _ai(system: str, user_msg: str, max_tokens: int = 600) -> str:
    if not OPENROUTER_API_KEY:
        return "AI Mentor is currently unavailable. Please configure OPENROUTER_API_KEY."
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways LMS",
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
        print(f"[LEARNING AI] Error: {e}", flush=True)
        return "I'm having trouble connecting right now. Please try again shortly."


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
    return dict(lesson)


@router.get("/lesson/{lesson_id}/navigation")
async def get_lesson_navigation(lesson_id: int, current_user=Depends(get_current_user)):
    """Get next and previous lessons for navigation"""
    current = await database.fetch_one(
        "SELECT l.id, l.module_id, l.order_index, m.level_id "
        "FROM learning_lessons l "
        "JOIN learning_modules m ON m.id = l.module_id "
        "WHERE l.id = :lid",
        {"lid": lesson_id}
    )
    if not current:
        raise HTTPException(404, "Lesson not found")
    
    prev_lesson = await database.fetch_one(
        "SELECT id, title FROM learning_lessons "
        "WHERE module_id = :mid AND order_index < :order "
        "ORDER BY order_index DESC LIMIT 1",
        {"mid": current["module_id"], "order": current["order_index"]}
    )
    
    next_lesson = await database.fetch_one(
        "SELECT id, title FROM learning_lessons "
        "WHERE module_id = :mid AND order_index > :order "
        "ORDER BY order_index ASC LIMIT 1",
        {"mid": current["module_id"], "order": current["order_index"]}
    )
    
    if not next_lesson:
        next_module = await database.fetch_one(
            "SELECT id FROM learning_modules "
            "WHERE level_id = :lid AND order_index > ("
            "  SELECT order_index FROM learning_modules WHERE id = :mid"
            ") ORDER BY order_index ASC LIMIT 1",
            {"lid": current["level_id"], "mid": current["module_id"]}
        )
        if next_module:
            next_lesson = await database.fetch_one(
                "SELECT id, title FROM learning_lessons "
                "WHERE module_id = :mid ORDER BY order_index ASC LIMIT 1",
                {"mid": next_module["id"]}
            )
    
    return {
        "prev_lesson": dict(prev_lesson) if prev_lesson else None,
        "next_lesson": dict(next_lesson) if next_lesson else None,
    }


@router.get("/quiz/{lesson_id}")
async def get_quiz(lesson_id: int, current_user=Depends(get_current_user)):
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


@router.get("/badges/{user_id}")
async def get_badges(user_id: int, current_user=Depends(get_current_user)):
    caller = _user_id(current_user)
    if caller != user_id and not current_user.get("is_admin"):
        raise HTTPException(403, "Forbidden")
    
    badges = await database.fetch_all(
        "SELECT badge_type, earned_at FROM user_badges WHERE user_id = :uid ORDER BY earned_at DESC",
        {"uid": user_id}
    )
    
    badge_info = {
        "beginner_complete": {"name": "Beginner Trader", "icon": "fa-seedling", "color": "green"},
        "intermediate_complete": {"name": "Technical Analyst", "icon": "fa-chart-line", "color": "blue"},
        "advanced_complete": {"name": "Strategy Builder", "icon": "fa-chess-knight", "color": "purple"},
        "academy_complete": {"name": "Pipways Certified Trader", "icon": "fa-certificate", "color": "yellow"},
        "first_quiz_pass": {"name": "Quiz Master", "icon": "fa-star", "color": "orange"},
        "perfect_quiz": {"name": "Perfect Score", "icon": "fa-trophy", "color": "gold"},
    }
    
    result = []
    for b in badges:
        info = badge_info.get(b["badge_type"], {"name": b["badge_type"], "icon": "fa-award", "color": "gray"})
        result.append({
            "type": b["badge_type"],
            "name": info["name"],
            "icon": info["icon"],
            "color": info["color"],
            "earned_at": b["earned_at"],
        })
    
    return result


@router.get("/ai-mentor/recommendations/{user_id}")
async def get_ai_mentor_recommendations(user_id: int, current_user=Depends(get_current_user)):
    caller = _user_id(current_user)
    if caller != user_id and not current_user.get("is_admin"):
        raise HTTPException(403, "Forbidden")
    
    try:
        trades = await database.fetch_all(
            "SELECT pair, direction, entry_price, exit_price, pnl, risk_percent, r_multiple, setup_type, outcome "
            "FROM trading_journal WHERE user_id = :uid ORDER BY created_at DESC LIMIT 50",
            {"uid": user_id}
        )
    except:
        trades = []
    
    total_trades = len(trades)
    wins = [t for t in trades if t["pnl"] and float(t["pnl"]) > 0]
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
    avg_risk = sum([float(t["risk_percent"] or 0) for t in trades]) / len(trades) if trades else 0
    
    issues = []
    if avg_risk > 3:
        issues.append("over-risking")
    
    recommendations = []
    for issue in issues[:2]:
        if issue == "over-risking":
            lesson = await database.fetch_one(
                "SELECT l.id, l.title, m.title as module_name FROM learning_lessons l "
                "JOIN learning_modules m ON m.id = l.module_id "
                "WHERE l.title ILIKE '%risk%' OR l.title ILIKE '%1-2%' "
                "ORDER BY m.order_index, l.order_index LIMIT 1"
            )
            if lesson:
                recommendations.append({
                    "lesson_id": lesson["id"],
                    "lesson_title": lesson["title"],
                    "module_name": lesson["module_name"],
                    "reason": f"Your average risk is {avg_risk:.1f}% per trade. Review risk management lessons.",
                    "priority": "high"
                })
    
    if not recommendations and total_trades > 0:
        next_lesson = await database.fetch_one(
            "SELECT l.id, l.title, m.title as module_name FROM learning_lessons l "
            "JOIN learning_modules m ON m.id = l.module_id "
            "WHERE l.id NOT IN ("
            "  SELECT lesson_id FROM user_learning_progress WHERE user_id = :uid AND completed = TRUE"
            ") ORDER BY m.level_id, m.order_index, l.order_index LIMIT 1",
            {"uid": user_id}
        )
        if next_lesson:
            recommendations.append({
                "lesson_id": next_lesson["id"],
                "lesson_title": next_lesson["title"],
                "module_name": next_lesson["module_name"],
                "reason": "Continue your learning journey.",
                "priority": "low"
            })
    
    return {
        "recommendations": recommendations,
        "trading_stats": {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 1),
            "avg_risk": round(avg_risk, 2),
            "identified_issues": issues
        }
    }


@router.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmission, current_user=Depends(get_current_user)):
    user_id = _user_id(current_user)

    questions = await database.fetch_all(
        "SELECT id, correct_answer, explanation, topic_slug FROM lesson_quizzes "
        "WHERE lesson_id=:lid ORDER BY id",
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
            "INSERT INTO user_quiz_results "
            "(user_id, lesson_id, question_id, selected_answer, is_correct, answered_at) "
            "VALUES (:uid, :lid, :qid, :ans, :ok, NOW())",
            {"uid": user_id, "lid": payload.lesson_id, "qid": q_id, "ans": selected, "ok": is_correct}
        )
        results.append({
            "question_id": q_id,
            "is_correct": is_correct,
            "correct_answer": row["correct_answer"],
            "explanation": row["explanation"],
        })

    score = round((correct / total * 100) if total else 0, 1)
    passed = score >= 70

    new_badge = None
    if passed:
        await _mark_lesson_complete(user_id, payload.lesson_id, score)
        new_badge = await _check_and_award_badges(user_id, payload.lesson_id, score, correct == total)
    
    await _update_learning_profile(user_id, wrong_slugs, correct_slugs)

    lesson = await database.fetch_one(
        "SELECT l.title, lv.name AS level_name FROM learning_lessons l "
        "JOIN learning_modules m ON m.id=l.module_id "
        "JOIN learning_levels lv ON lv.id=m.level_id "
        "WHERE l.id=:lid",
        {"lid": payload.lesson_id}
    )
    
    feedback = await _quiz_feedback(score, passed, lesson["title"] if lesson else "this lesson",
                                   wrong_slugs, lesson["level_name"].lower() if lesson else "intermediate")

    return {
        "score": score,
        "correct": correct,
        "total": total,
        "passed": passed,
        "results": results,
        "mentor_feedback": feedback,
        "new_badge": new_badge,
    }


@router.post("/lesson/complete")
async def complete_lesson(payload: LessonCompleteRequest, current_user=Depends(get_current_user)):
    user_id = _user_id(current_user)
    await _mark_lesson_complete(user_id, payload.lesson_id, payload.quiz_score)
    return {"success": True}


@router.get("/mentor/guide/{user_id}")
async def mentor_guide(user_id: int, current_user=Depends(get_current_user)):
    caller = _user_id(current_user)
    if caller != user_id and not current_user.get("is_admin"):
        raise HTTPException(403, "Forbidden")

    progress = await database.fetch_all(
        "SELECT p.lesson_id, p.completed, p.quiz_score, l.title "
        "FROM user_learning_progress p JOIN learning_lessons l ON l.id=p.lesson_id "
        "WHERE p.user_id=:uid",
        {"uid": user_id}
    )
    profile = await database.fetch_one(
        "SELECT weak_topics, strong_topics FROM user_learning_profile WHERE user_id=:uid",
        {"uid": user_id}
    )

    done = [r["title"] for r in progress if r["completed"]]
    weak = _parse_json(profile["weak_topics"]) if profile else []
    strong = _parse_json(profile["strong_topics"]) if profile else []

    next_lesson = await database.fetch_one(
        "SELECT l.id, l.title, m.title AS module_title "
        "FROM learning_lessons l JOIN learning_modules m ON m.id=l.module_id "
        "WHERE l.id NOT IN ("
        "  SELECT lesson_id FROM user_learning_progress WHERE user_id=:uid AND completed=TRUE"
        ") ORDER BY m.order_index, l.order_index LIMIT 1",
        {"uid": user_id}
    )

    ctx = f"Completed lessons ({len(done)}): {', '.join(done) or 'none yet'}. Weak topics: {', '.join(weak) or 'none'}. Next: {next_lesson['title'] + ' in ' + next_lesson['module_title'] if next_lesson else 'all done'}."
    system = "You are the Pipways Trading Coach. Give a warm 2-3 sentence coaching message. Be encouraging and specific."
    message = await _ai(system, f"Coaching context:\n{ctx}")

    return {
        "message": message,
        "next_lesson": dict(next_lesson) if next_lesson else None,
        "completed_count": len(done),
        "weak_topics": weak,
    }


@router.post("/mentor/teach")
async def mentor_teach(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    user_id = _user_id(current_user)
    lesson = await database.fetch_one(
        "SELECT l.title, l.content, m.title AS module_title, lv.name AS level_name "
        "FROM learning_lessons l "
        "JOIN learning_modules m ON m.id=l.module_id "
        "JOIN learning_levels lv ON lv.id=m.level_id "
        "WHERE l.id=:lid",
        {"lid": lesson_id}
    )
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    profile = await database.fetch_one(
        "SELECT weak_topics FROM user_learning_profile WHERE user_id=:uid", {"uid": user_id}
    )
    weak = _parse_json(profile["weak_topics"]) if profile else []
    level = lesson["level_name"].lower()

    tone = {
        "beginner": "Use very simple language and real-world analogies. Avoid jargon entirely.",
        "intermediate": "Use technical terms with clear definitions. Connect concepts to chart examples.",
        "advanced": "Use institutional terminology. Discuss market structure, liquidity and order flow.",
    }.get(level, "Use clear, professional language.")

    system = f"You are the Pipways Trading Coach. Teaching style: {tone} Structure: 1) Warm opening. 2) Core concept. 3) Step-by-step breakdown. 4) Trade example. 5) Common pitfall. 6) Summary. Keep under 450 words."
    user_msg = f"Teach this lesson: {lesson['title']} ({lesson['module_title']})\n\nContext:\n{lesson['content'][:1200]}\n\nUser weak topics: {', '.join(weak) or 'none'}."

    explanation = await _ai(system, user_msg)

    return {
        "lesson_title": lesson["title"],
        "module_title": lesson["module_title"],
        "level": lesson["level_name"],
        "explanation": explanation,
    }


@router.post("/mentor/practice")
async def mentor_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
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

    system = "You are the Pipways Trading Coach. Create ONE short, realistic practice exercise. Format: Scenario (1-2 sentences) → Question → blank line → Model Answer. Use different currency pairs each time. Under 180 words."
    exercise = await _ai(
        system,
        f"Create practice exercise for '{lesson['title']}' at {lesson['level_name']} level.\nContext: {lesson['content'][:600]}"
    )

    return {"lesson_title": lesson["title"], "exercise": exercise}


@router.post("/mentor/chart-practice")
async def mentor_chart_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
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

    system = 'You create chart exercises. Return ONLY valid JSON with keys: tv_symbol (e.g., "FX:EURUSD"), tv_interval (15, 60, 240, D), scenario (max 80 words), question, options (array of 4 strings), correct (A/B/C/D), explanation. No text outside JSON.'
    level = lesson["level_name"].lower()
    complexity = {
        "beginner": "basic support/resistance",
        "intermediate": "support/resistance with trend context",
        "advanced": "order blocks, liquidity sweeps",
    }.get(level, "support and resistance")

    raw = await _ai(system, f"Create chart exercise about '{lesson['title']}' focusing on {complexity}.")

    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
    except Exception:
        data = {
            "tv_symbol": "FX:EURUSD",
            "tv_interval": "240",
            "scenario": "EUR/USD H4 chart in uptrend, pulling back to support at 1.0850.",
            "question": "What would you expect at the 1.0850 support?",
            "options": ["A: Buy the bounce", "B: Sell into pullback", "C: Wait", "D: No trade"],
            "correct": "A",
            "explanation": "In an uptrend, pullbacks to support offer high-probability long entries.",
        }

    return {
        "lesson_title": lesson["title"],
        "level": lesson["level_name"],
        "chart_practice": data,
    }


def _parse_json(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except Exception:
        return []


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
            {"uid": user_id, "lv": lesson["level_id"], "mid": lesson["module_id"], "lid": lesson_id, "score": score}
        )


async def _update_learning_profile(user_id: int, wrong_slugs: list, correct_slugs: list) -> None:
    existing = await database.fetch_one(
        "SELECT weak_topics, strong_topics FROM user_learning_profile WHERE user_id=:uid",
        {"uid": user_id}
    )
    if existing:
        cur_weak = _parse_json(existing["weak_topics"])
        cur_strong = _parse_json(existing["strong_topics"])
        new_weak = list(set(cur_weak + wrong_slugs) - set(correct_slugs))
        new_strong = list(set(cur_strong + correct_slugs))
        await database.execute(
            "UPDATE user_learning_profile "
            "SET weak_topics=:w, strong_topics=:s, last_updated=NOW() WHERE user_id=:uid",
            {"uid": user_id, "w": json.dumps(new_weak), "s": json.dumps(new_strong)}
        )
    else:
        await database.execute(
            "INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, last_updated) "
            "VALUES (:uid, :w, :s, NOW())",
            {"uid": user_id, "w": json.dumps(list(set(wrong_slugs))), "s": json.dumps(list(set(correct_slugs)))}
        )


async def _check_and_award_badges(user_id: int, lesson_id: int, score: float, perfect: bool):
    new_badge = None
    lesson = await database.fetch_one(
        "SELECT m.level_id FROM learning_lessons l "
        "JOIN learning_modules m ON m.id = l.module_id WHERE l.id = :lid",
        {"lid": lesson_id}
    )
    if not lesson:
        return None
    
    level_id = lesson["level_id"]
    
    existing_badges = await database.fetch_all(
        "SELECT badge_type FROM user_badges WHERE user_id = :uid",
        {"uid": user_id}
    )
    existing_types = {b["badge_type"] for b in existing_badges}
    
    if "first_quiz_pass" not in existing_types:
        await database.execute(
            "INSERT INTO user_badges (user_id, badge_type, earned_at) VALUES (:uid, :type, NOW())",
            {"uid": user_id, "type": "first_quiz_pass"}
        )
        new_badge = {"type": "first_quiz_pass", "name": "Quiz Master"}
    
    if perfect and "perfect_quiz" not in existing_types:
        await database.execute(
            "INSERT INTO user_badges (user_id, badge_type, earned_at) VALUES (:uid, :type, NOW())",
            {"uid": user_id, "type": "perfect_quiz"}
        )
        new_badge = {"type": "perfect_quiz", "name": "Perfect Score"}
    
    level_lessons = await database.fetch_val(
        "SELECT COUNT(*) FROM learning_lessons l "
        "JOIN learning_modules m ON m.id = l.module_id WHERE m.level_id = :lid",
        {"lid": level_id}
    )
    completed_lessons = await database.fetch_val(
        "SELECT COUNT(*) FROM user_learning_progress p "
        "JOIN learning_lessons l ON l.id = p.lesson_id "
        "JOIN learning_modules m ON m.id = l.module_id "
        "WHERE p.user_id = :uid AND m.level_id = :lid AND p.completed = TRUE",
        {"uid": user_id, "lid": level_id}
    )
    
    if level_lessons == completed_lessons:
        level_names = {1: "beginner_complete", 2: "intermediate_complete", 3: "advanced_complete"}
        badge_name = level_names.get(level_id)
        if badge_name and badge_name not in existing_types:
            await database.execute(
                "INSERT INTO user_badges (user_id, badge_type, earned_at) VALUES (:uid, :type, NOW())",
                {"uid": user_id, "type": badge_name}
            )
            badge_display = {
                "beginner_complete": "Beginner Trader",
                "intermediate_complete": "Technical Analyst",
                "advanced_complete": "Strategy Builder"
            }
            new_badge = {"type": badge_name, "name": badge_display.get(badge_name)}
            
            all_complete = True
            for lid in [1, 2, 3]:
                lvl_total = await database.fetch_val(
                    "SELECT COUNT(*) FROM learning_lessons l "
                    "JOIN learning_modules m ON m.id = l.module_id WHERE m.level_id = :lid",
                    {"lid": lid}
                )
                lvl_done = await database.fetch_val(
                    "SELECT COUNT(*) FROM user_learning_progress p "
                    "JOIN learning_lessons l ON l.id = p.lesson_id "
                    "JOIN learning_modules m ON m.id = l.module_id "
                    "WHERE p.user_id = :uid AND m.level_id = :lid AND p.completed = TRUE",
                    {"uid": user_id, "lid": lid}
                )
                if lvl_total != lvl_done:
                    all_complete = False
                    break
            
            if all_complete and "academy_complete" not in existing_types:
                await database.execute(
                    "INSERT INTO user_badges (user_id, badge_type, earned_at) VALUES (:uid, :type, NOW())",
                    {"uid": user_id, "type": "academy_complete"}
                )
                new_badge = {"type": "academy_complete", "name": "Pipways Certified Trader"}
    
    return new_badge


async def _quiz_feedback(score: float, passed: bool, lesson_title: str, wrong_slugs: list, level: str) -> str:
    if not OPENROUTER_API_KEY:
        if passed:
            return f"Excellent! You scored {score}% and completed '{lesson_title}'."
        return f"You scored {score}%. You need 70% to pass. Review and try again!"

    tone = {
        "beginner": "Be very encouraging and gentle. Use simple language.",
        "intermediate": "Be professional and direct.",
        "advanced": "Be concise and analytical.",
    }.get(level, "Be encouraging.")

    slugs = ", ".join(set(wrong_slugs)) if wrong_slugs else "none"
    status = "passed" if passed else f"did not pass (scored {score}%, need 70%)"

    system = f"You are the Pipways Trading Coach. {tone} Write 2-3 sentences of quiz feedback. End with a specific action."
    return await _ai(
        system,
        f"Student scored {score}% on '{lesson_title}' and {status}. Wrong topics: {slugs}."
    )


@router.get("/health")
async def lms_health():
    result = {}
    tables = [
        "learning_levels", "learning_modules", "learning_lessons",
        "lesson_quizzes", "user_learning_progress", "user_quiz_results",
        "user_learning_profile", "user_badges"
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
        "tip": "Call POST /learning/admin/seed if curriculum is empty."
    }


@router.post("/admin/seed")
async def admin_seed_curriculum(current_user=Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(403, "Admin access required")

    try:
        from .lms_init import _seed_curriculum, init_lms_tables
        await init_lms_tables()
        count = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
        if count > 0:
            return {"status": "already_seeded", "levels": int(count), "message": "Curriculum exists."}
        await _seed_curriculum()
        final = await database.fetch_val("SELECT COUNT(*) FROM learning_levels")
        return {"status": "seeded", "levels": int(final), "message": f"Curriculum seeded: {final} levels."}
    except Exception as e:
        raise HTTPException(500, f"Seed failed: {e}")
