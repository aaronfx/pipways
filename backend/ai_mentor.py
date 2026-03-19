"""
AI Mentor Service with Trading Academy Integration
Ensures every response includes relevant lesson recommendations
"""

import os
import json
import httpx
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from .security import get_current_user
from .database import database

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class LessonRecommendation(BaseModel):
    type: str  # "lesson" | "module" | "level"
    title: str
    description: str
    url: str
    metadata: Dict[str, Any]
    reason: str  # "recommended" | "next_step" | "foundational"

class MentorResponse(BaseModel):
    response: str
    recommendations: List[LessonRecommendation]
    academy_progress: Optional[Dict[str, Any]] = None

async def fetch_academy_structure() -> Dict:
    """Fetch full academy hierarchy from database"""
    try:
        levels = await database.fetch_all(
            "SELECT id, name, description, order_index FROM learning_levels ORDER BY order_index"
        )
        structure = {"levels": []}

        for level in levels:
            modules = await database.fetch_all(
                """SELECT id, title, description, order_index 
                   FROM learning_modules 
                   WHERE level_id = :lid ORDER BY order_index""",
                {"lid": level["id"]}
            )
            level_modules = []

            for module in modules:
                lessons = await database.fetch_all(
                    """SELECT id, title, order_index 
                       FROM learning_lessons 
                       WHERE module_id = :mid ORDER BY order_index""",
                    {"mid": module["id"]}
                )
                mod_dict = dict(module)
                mod_dict["lessons"] = [dict(l) for l in lessons]
                level_modules.append(mod_dict)

            level_dict = dict(level)
            level_dict["modules"] = level_modules
            structure["levels"].append(level_dict)

        return structure
    except Exception as e:
        print(f"[ACADEMY FETCH ERROR] {e}")
        return {"levels": []}

async def fetch_user_academy_progress(user_id: int) -> Dict:
    """Fetch user's progress through academy"""
    try:
        total_lessons = await database.fetch_val(
            "SELECT COUNT(*) FROM learning_lessons"
        ) or 0

        completed = await database.fetch_val(
            """SELECT COUNT(*) FROM user_learning_progress 
               WHERE user_id = :uid AND completed = TRUE""",
            {"uid": user_id}
        ) or 0

        # Find next incomplete lesson
        next_lesson = await database.fetch_one(
            """SELECT l.id, l.title, m.title as module_title, lv.name as level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id = l.module_id
               JOIN learning_levels lv ON lv.id = m.level_id
               WHERE NOT EXISTS (
                   SELECT 1 FROM user_learning_progress p
                   WHERE p.lesson_id = l.id AND p.user_id = :uid AND p.completed = TRUE
               )
               ORDER BY lv.order_index, m.order_index, l.order_index
               LIMIT 1""",
            {"uid": user_id}
        )

        return {
            "completion_rate": round((completed / total_lessons * 100) if total_lessons else 0, 1),
            "completed_lessons": completed,
            "total_lessons": total_lessons,
            "current_level": next_lesson["level_name"] if next_lesson else "Beginner",
            "next_lesson": dict(next_lesson) if next_lesson else None
        }
    except Exception as e:
        print(f"[PROGRESS FETCH ERROR] {e}")
        return {"completion_rate": 0, "next_lesson": None}

def find_relevant_lessons(question: str, academy_structure: Dict) -> List[Dict]:
    """Keyword matching to find lessons related to user question"""
    question_lower = question.lower()
    keywords = {
        "foundation": ["foundation", "beginner", "start", "basic", "forex", "introduction"],
        "support_resistance": ["support", "resistance", "s/r", "levels", "supply", "demand"],
        "trend": ["trend", "direction", "uptrend", "downtrend", "higher high"],
        "pattern": ["pattern", "candlestick", "pin bar", "engulfing", "head and shoulders"],
        "indicator": ["rsi", "macd", "indicator", "oscillator", "moving average"],
        "risk": ["risk", "management", "stop loss", "take profit", "position size", "lot size"],
        "smc": ["smc", "smart money", "order block", "liquidity", "ict", "institutional"],
        "fibonacci": ["fib", "fibonacci", "retracement", "extension", "golden ratio"],
        "psychology": ["psychology", "emotions", "discipline", "mindset", "fear", "greed"],
        "strategy": ["strategy", "system", "backtest", "trading plan", "edge"]
    }

    matched_lessons = []
    seen_ids = set()

    # Determine which keyword categories match
    matching_categories = []
    for category, terms in keywords.items():
        if any(term in question_lower for term in terms):
            matching_categories.append(category)

    # Search through academy structure
    for level in academy_structure.get("levels", []):
        for module in level.get("modules", []):
            module_title = module.get("title", "").lower()
            for lesson in module.get("lessons", []):
                lesson_title = lesson.get("title", "").lower()
                combined_text = f"{module_title} {lesson_title}"

                # Check if lesson matches any category
                score = 0
                for category in matching_categories:
                    if any(term in combined_text for term in keywords[category]):
                        score += 1

                # Also check direct keyword presence
                if any(word in question_lower for word in lesson_title.split()):
                    score += 0.5

                if score > 0 and lesson["id"] not in seen_ids:
                    lesson["score"] = score
                    lesson["level_name"] = level["name"]
                    lesson["module_title"] = module["title"]
                    matched_lessons.append(lesson)
                    seen_ids.add(lesson["id"])

    # Sort by relevance score
    matched_lessons.sort(key=lambda x: x.get("score", 0), reverse=True)
    return matched_lessons[:3]  # Top 3 matches

async def get_next_lessons(user_id: int, academy_structure: Dict, limit: int = 2) -> List[Dict]:
    """Get next sequential lessons for user"""
    try:
        # Find first incomplete lesson
        next_lesson_row = await database.fetch_one(
            """SELECT l.id, l.title, l.module_id, m.title as module_title, 
                      lv.name as level_name, lv.id as level_id
               FROM learning_lessons l
               JOIN learning_modules m ON m.id = l.module_id
               JOIN learning_levels lv ON lv.id = m.level_id
               WHERE NOT EXISTS (
                   SELECT 1 FROM user_learning_progress p
                   WHERE p.lesson_id = l.id AND p.user_id = :uid AND p.completed = TRUE
               )
               ORDER BY lv.order_index, m.order_index, l.order_index
               LIMIT :limit""",
            {"uid": user_id, "limit": limit}
        )

        if not next_lesson_row:
            return []

        return [dict(next_lesson_row)]
    except Exception as e:
        print(f"[NEXT LESSON ERROR] {e}")
        return []

def ensure_lesson_recommendations(
    recommendations: List[Dict], 
    academy_structure: Dict, 
    user_id: int,
    question: str
) -> List[LessonRecommendation]:
    """CRITICAL: Always returns at least 1 lesson recommendation"""

    # If we have recommendations from AI, use those
    if recommendations and len(recommendations) > 0:
        return [LessonRecommendation(**rec) for rec in recommendations]

    # Otherwise, find relevant lessons based on keywords
    relevant = find_relevant_lessons(question, academy_structure)

    if relevant:
        return [
            LessonRecommendation(
                type="lesson",
                title=lesson["title"],
                description=f"{lesson['level_name']} • {lesson['module_title']}",
                url=f"/academy.html?lesson={lesson['id']}",
                metadata={"lesson_id": lesson["id"], "module_id": lesson.get("module_id")},
                reason="recommended"
            )
            for lesson in relevant[:2]
        ]

    # Last resort: return first lesson of academy
    for level in academy_structure.get("levels", []):
        for module in level.get("modules", []):
            if module.get("lessons"):
                first = module["lessons"][0]
                return [
                    LessonRecommendation(
                        type="lesson",
                        title=first["title"],
                        description=f"{level['name']} • {module['title']}",
                        url=f"/academy.html?lesson={first['id']}",
                        metadata={"lesson_id": first["id"]},
                        reason="foundational"
                    )
                ]

    return []

async def generate_ai_response(message: str, context: Dict) -> str:
    """Generate brief AI response (max 150 words)"""
    if not OPENROUTER_API_KEY:
        return "Welcome to Forex trading! Check out the recommended lesson below to learn more. 👇"

    system_prompt = """You are a concise Forex trading mentor. Rules:
- Maximum 150 words, 2-3 short paragraphs
- Always end by referencing the lesson card shown below
- Be encouraging but brief
- Focus on practical next steps"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways AI Mentor",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "max_tokens": 250,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ]
                }
            )
            data = res.json()
            text = data["choices"][0]["message"]["content"].strip()

            # Truncate if too long (max 500 chars)
            if len(text) > 500:
                text = text[:497] + "..."

            return text
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return "Great question! Learn the complete answer in the lesson below. 👇"

@router.post("/mentor/ask", response_model=MentorResponse)
async def ask_mentor(
    chat: ChatMessage,
    current_user = Depends(get_current_user)
):
    """Main mentor endpoint - always returns lesson recommendations"""
    user_id = current_user.get("id") if current_user else None

    # Fetch academy data in parallel
    academy_structure = await fetch_academy_structure()
    user_progress = await fetch_user_academy_progress(user_id) if user_id else None

    # Generate AI response (brief)
    ai_text = await generate_ai_response(chat.message, chat.context or {})

    # Get recommendations
    recommendations = []

    # 1. Find relevant lessons based on query
    relevant = find_relevant_lessons(chat.message, academy_structure)
    for lesson in relevant[:2]:
        recommendations.append({
            "type": "lesson",
            "title": lesson["title"],
            "description": f"{lesson['level_name']} • {lesson['module_title']}",
            "url": f"/academy.html?lesson={lesson['id']}",
            "metadata": {"lesson_id": lesson["id"]},
            "reason": "recommended"
        })

    # 2. Add next sequential lesson if space available
    if user_id and len(recommendations) < 3:
        next_lessons = await get_next_lessons(user_id, academy_structure, limit=1)
        if next_lessons:
            nl = next_lessons[0]
            # Only add if not already in recommendations
            if not any(r["metadata"].get("lesson_id") == nl["id"] for r in recommendations):
                recommendations.append({
                    "type": "lesson",
                    "title": nl["title"],
                    "description": f"Continue: {nl['level_name']} • {nl['module_title']}",
                    "url": f"/academy.html?lesson={nl['id']}",
                    "metadata": {"lesson_id": nl["id"]},
                    "reason": "next_step"
                })

    # 3. Ensure at least one recommendation
    if not recommendations:
        # Fallback to first beginner lesson
        for level in academy_structure.get("levels", []):
            if level["name"].lower() == "beginner":
                for module in level.get("modules", []):
                    if module.get("lessons"):
                        first = module["lessons"][0]
                        recommendations.append({
                            "type": "lesson",
                            "title": first["title"],
                            "description": f"Start here: {module['title']}",
                            "url": f"/academy.html?lesson={first['id']}",
                            "metadata": {"lesson_id": first["id"]},
                            "reason": "foundational"
                        })
                        break
                break

    return MentorResponse(
        response=ai_text,
        recommendations=[LessonRecommendation(**r) for r in recommendations],
        academy_progress=user_progress
    )

@router.post("/mentor/track-lesson-click")
async def track_lesson_click(
    lesson_id: int,
    current_user = Depends(get_current_user)
):
    """Track when user clicks a lesson recommendation"""
    try:
        user_id = current_user.get("id") if current_user else None
        if user_id:
            await database.execute(
                """INSERT INTO user_activity (user_id, activity_type, metadata, created_at)
                   VALUES (:uid, 'lesson_click', :meta, NOW())""",
                {"uid": user_id, "meta": json.dumps({"lesson_id": lesson_id})}
            )
        return {"success": True}
    except Exception as e:
        print(f"[TRACK ERROR] {e}")
        return {"success": False}
