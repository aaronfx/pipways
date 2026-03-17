"""
Pipways LMS — Learning Router  v2  (learning.py)
All structured-learning API endpoints.
NEW file — zero changes to any existing module.

Mount in main.py:
    from . import learning
    app.include_router(learning.router, prefix="/learning", tags=["Learning"])
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
        "SELECT weak_topics, strong_topics, last_updated "
        "FROM user_learning_profile WHERE user_id=:uid",
        {"uid": user_id}
    )
    if not row:
        return {"user_id": user_id, "weak_topics": [], "strong_topics": [], "last_updated": None}
    return {
        "user_id":       user_id,
        "weak_topics":   _parse_json(row["weak_topics"]),
        "strong_topics": _parse_json(row["strong_topics"]),
        "last_updated":  row["last_updated"],
    }


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
    - Returns AI mentor feedback
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
    }


@router.post("/lesson/complete")
async def complete_lesson(payload: LessonCompleteRequest, current_user=Depends(get_current_user)):
    user_id = _user_id(current_user)
    await _mark_lesson_complete(user_id, payload.lesson_id, payload.quiz_score)
    return {"success": True}


@router.post("/profile/update")
async def update_profile(payload: ProfileUpdateRequest, current_user=Depends(get_current_user)):
    user_id = _user_id(current_user)
    await _upsert_profile(user_id, json.dumps(payload.weak_topics), json.dumps(payload.strong_topics))
    return {"success": True}


# ══════════════════════════════════════════════════════════════════════════════
# AI MENTOR ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/mentor/guide/{user_id}")
async def mentor_guide(user_id: int, current_user=Depends(get_current_user)):
    """
    Read user progress & profile → LLM → personalised coaching message.
    Called automatically when the Academy homepage loads.
    """
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

    done   = [r["title"] for r in progress if r["completed"]]
    weak   = _parse_json(profile["weak_topics"])  if profile else []
    strong = _parse_json(profile["strong_topics"]) if profile else []

    next_lesson = await database.fetch_one(
        "SELECT l.id, l.title, m.title AS module_title "
        "FROM learning_lessons l JOIN learning_modules m ON m.id=l.module_id "
        "WHERE l.id NOT IN ("
        "  SELECT lesson_id FROM user_learning_progress WHERE user_id=:uid AND completed=TRUE"
        ") ORDER BY m.order_index, l.order_index LIMIT 1",
        {"uid": user_id}
    )

    ctx = (
        f"Completed lessons ({len(done)}): {', '.join(done) or 'none yet'}. "
        f"Weak topics: {', '.join(weak) or 'none'}. "
        f"Strong topics: {', '.join(strong) or 'none'}. "
        f"Next lesson: {next_lesson['title'] + ' in ' + next_lesson['module_title'] if next_lesson else 'all done!'}."
    )
    system = (
        "You are the Pipways AI Trading Mentor. "
        "Give a warm 2–3 sentence coaching message based on the learner's progress. "
        "Be encouraging, specific, and end with a clear next action."
    )
    message = await _ai(system, f"Coaching context:\n{ctx}")

    return {
        "message":         message,
        "next_lesson":     dict(next_lesson) if next_lesson else None,
        "completed_count": len(done),
        "weak_topics":     weak,
    }


@router.post("/mentor/teach")
async def mentor_teach(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    """
    AI Mentor explains a lesson, adapting to the user's level and weak topics.
    Teaching style follows the BabyPips-style instructional structure.
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
        "beginner":     "Use very simple language and real-world analogies. Avoid jargon entirely.",
        "intermediate": "Use technical terms with clear definitions. Connect concepts to chart examples.",
        "advanced":     "Use institutional terminology. Discuss market structure, liquidity and order flow.",
    }.get(level, "Use clear, professional language.")

    system = (
        "You are the Pipways AI Trading Mentor. "
        f"Teaching style: {tone} "
        "Structure your explanation exactly as: "
        "1) Warm opening (1 sentence). "
        "2) Core concept — one clear sentence. "
        "3) Step-by-step breakdown (numbered). "
        "4) Trade example (pair, entry, stop, target). "
        "5) One common pitfall. "
        "6) Quick summary (1 sentence). "
        "Keep response under 450 words."
    )
    user_msg = (
        f"Teach this lesson: {lesson['title']} ({lesson['module_title']})\n\n"
        f"Reference content:\n{lesson['content'][:1200]}\n\n"
        f"User's weak topics to reinforce: {', '.join(weak) or 'none identified'}."
    )

    explanation = await _ai(system, user_msg)

    return {
        "lesson_title":  lesson["title"],
        "module_title":  lesson["module_title"],
        "level":         lesson["level_name"],
        "explanation":   explanation,
    }


@router.post("/mentor/practice")
async def mentor_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    """Generate a unique practice scenario exercise for the lesson."""
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
        "You are a trading coach. Create ONE short, realistic practice exercise. "
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
    Chart-based practice exercise.
    Returns a textual chart scenario the user interprets,
    then the mentor reveals and explains the correct answer.
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
        "Generate a realistic scenario describing what is visible on a chart. "
        "Format your response as valid JSON with exactly these keys: "
        '{"scenario": "...", "question": "...", "options": ["A: ...", "B: ...", "C: ...", "D: ..."], '
        '"correct": "A", "explanation": "..."}. '
        "Use a real currency pair. Keep scenario under 80 words. No extra text outside the JSON."
    )
    level = lesson["level_name"].lower()
    complexity = {
        "beginner":     "basic support/resistance or trend identification",
        "intermediate": "support/resistance with trend context, entry signals",
        "advanced":     "order blocks, liquidity sweeps, market structure",
    }.get(level, "support and resistance")

    raw = await _ai(system, f"Create a chart exercise about '{lesson['title']}' focusing on {complexity}.")

    try:
        clean = raw.strip().strip("```json").strip("```").strip()
        data  = json.loads(clean)
    except Exception:
        data = {
            "scenario":    f"EUR/USD H4 chart. Price has been in an uptrend and is pulling back to a key level.",
            "question":    f"Based on the uptrend context, what would you expect at this level?",
            "options":     ["A: Buy the bounce (trend continuation)", "B: Sell into the pullback", "C: Wait for more data", "D: No trade"],
            "correct":     "A",
            "explanation": "In an uptrend, pullbacks to support offer high-probability long entries with the trend.",
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
            "INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, last_updated) "
            "VALUES (:uid, :w, :s, NOW())",
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
            "INSERT INTO user_learning_profile (user_id, weak_topics, strong_topics, last_updated) "
            "VALUES (:uid, :w, :s, NOW())",
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
        f"You are the Pipways AI Trading Mentor. {tone} "
        "Write 2–3 sentences of quiz feedback. End with a specific action."
    )
    return await _ai(
        system,
        f"Student scored {score}% on '{lesson_title}' and {status}. "
        f"Topics with wrong answers: {slugs}."
    )
