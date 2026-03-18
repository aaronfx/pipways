"""
Pipways Trading Academy API Routes
Handles badges, progress, mentor guides, and quiz submissions
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from .database import database
from .lms_init import init_lms_tables
import json

router = APIRouter(prefix="/learning", tags=["learning"])

# Pydantic models
class QuizSubmission(BaseModel):
    user_id: int
    lesson_id: int
    question_id: int
    selected_answer: str
    is_correct: bool

class ProgressUpdate(BaseModel):
    user_id: int
    lesson_id: int
    completed: bool = True
    quiz_score: Optional[float] = None

class MentorRequest(BaseModel):
    user_id: int
    level_id: int
    topic: str
    question: str

# Dependency to ensure tables exist
async def ensure_tables():
    await init_lms_tables()

@router.get("/levels")
async def get_levels():
    """Get all learning levels with modules"""
    query = """
        SELECT 
            ll.id as level_id,
            ll.name as level_name,
            ll.description as level_desc,
            lm.id as module_id,
            lm.title as module_title,
            lm.description as module_desc,
            lls.id as lesson_id,
            lls.title as lesson_title,
            lls.content as lesson_content,
            lls.order_index as lesson_order
        FROM learning_levels ll
        LEFT JOIN learning_modules lm ON lm.level_id = ll.id
        LEFT JOIN learning_lessons lls ON lls.module_id = lm.id
        ORDER BY ll.order_index, lm.order_index, lls.order_index
    """
    rows = await database.fetch_all(query)
    
    # Organize into hierarchical structure
    levels = {}
    for row in rows:
        level_id = row['level_id']
        if level_id not in levels:
            levels[level_id] = {
                "id": level_id,
                "name": row['level_name'],
                "description": row['level_desc'],
                "modules": {}
            }
        
        module_id = row['module_id']
        if module_id and module_id not in levels[level_id]['modules']:
            levels[level_id]['modules'][module_id] = {
                "id": module_id,
                "title": row['module_title'],
                "description": row['module_desc'],
                "lessons": []
            }
        
        if row['lesson_id']:
            levels[level_id]['modules'][module_id]['lessons'].append({
                "id": row['lesson_id'],
                "title": row['lesson_title'],
                "content": row['lesson_content'],
                "order": row['lesson_order']
            })
    
    # Convert to list
    return list(levels.values())

@router.get("/modules/{level_id}")
async def get_modules(level_id: int):
    """Get modules for a specific level"""
    query = """
        SELECT * FROM learning_modules 
        WHERE level_id = :level_id 
        ORDER BY order_index
    """
    return await database.fetch_all(query, {"level_id": level_id})

@router.get("/lessons/{module_id}")
async def get_lessons(module_id: int):
    """Get lessons for a specific module"""
    query = """
        SELECT * FROM learning_lessons 
        WHERE module_id = :module_id 
        ORDER BY order_index
    """
    return await database.fetch_all(query, {"module_id": module_id})

@router.get("/lesson/{lesson_id}/quizzes")
async def get_lesson_quizzes(lesson_id: int):
    """Get quizzes for a lesson"""
    query = """
        SELECT * FROM lesson_quizzes 
        WHERE lesson_id = :lesson_id
    """
    quizzes = await database.fetch_all(query, {"lesson_id": lesson_id})
    return [dict(q) for q in quizzes]

@router.post("/quiz/submit")
async def submit_quiz(submission: QuizSubmission):
    """Submit a quiz answer"""
    # Save result
    query = """
        INSERT INTO user_quiz_results 
        (user_id, lesson_id, question_id, selected_answer, is_correct)
        VALUES (:user_id, :lesson_id, :question_id, :selected_answer, :is_correct)
        ON CONFLICT (user_id, question_id) DO UPDATE SET
        selected_answer = EXCLUDED.selected_answer,
        is_correct = EXCLUDED.is_correct,
        answered_at = NOW()
    """
    await database.execute(query, dict(submission))
    
    # Check if all quizzes completed for lesson
    progress_query = """
        SELECT COUNT(*) as total,
               SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
        FROM user_quiz_results
        WHERE user_id = :user_id AND lesson_id = :lesson_id
    """
    progress = await database.fetch_one(progress_query, {
        "user_id": submission.user_id,
        "lesson_id": submission.lesson_id
    })
    
    return {
        "submitted": True,
        "is_correct": submission.is_correct,
        "progress": dict(progress) if progress else {"total": 0, "correct": 0}
    }

@router.get("/progress/{user_id}")
async def get_user_progress(user_id: int):
    """Get user's learning progress"""
    # Initialize profile if not exists
    profile_query = """
        INSERT INTO user_learning_profile (user_id, first_academy_visit)
        VALUES (:user_id, FALSE)
        ON CONFLICT (user_id) DO UPDATE SET
        last_updated = NOW()
        RETURNING *
    """
    await database.fetch_one(profile_query, {"user_id": user_id})
    
    # Get progress
    query = """
        SELECT 
            lls.id as lesson_id,
            lls.module_id,
            lm.level_id,
            lls.title,
            COALESCE(ulp.completed, FALSE) as completed,
            ulp.quiz_score,
            ulp.completed_at
        FROM learning_lessons lls
        JOIN learning_modules lm ON lm.id = lls.module_id
        LEFT JOIN user_learning_progress ulp 
            ON ulp.lesson_id = lls.id AND ulp.user_id = :user_id
        ORDER BY lm.level_id, lm.order_index, lls.order_index
    """
    progress = await database.fetch_all(query, {"user_id": user_id})
    
    # Calculate stats
    total_lessons = len(progress)
    completed_lessons = sum(1 for p in progress if p['completed'])
    completion_rate = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    return {
        "user_id": user_id,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "completion_rate": round(completion_rate, 1),
        "lessons": [dict(p) for p in progress]
    }

@router.post("/progress/update")
async def update_progress(update: ProgressUpdate):
    """Update lesson progress"""
    query = """
        INSERT INTO user_learning_progress 
        (user_id, lesson_id, completed, quiz_score, completed_at)
        VALUES (:user_id, :lesson_id, :completed, :quiz_score, 
                CASE WHEN :completed THEN NOW() ELSE NULL END)
        ON CONFLICT (user_id, lesson_id) DO UPDATE SET
        completed = EXCLUDED.completed,
        quiz_score = COALESCE(EXCLUDED.quiz_score, user_learning_progress.quiz_score),
        completed_at = COALESCE(EXCLUDED.completed_at, user_learning_progress.completed_at)
    """
    await database.execute(query, dict(update))
    return {"updated": True}

@router.get("/badges/{user_id}")
async def get_user_badges(user_id: int):
    """Get user's earned badges"""
    query = """
        SELECT * FROM user_badges 
        WHERE user_id = :user_id 
        ORDER BY earned_at DESC
    """
    badges = await database.fetch_all(query, {"user_id": user_id})
    
    # Define all available badges
    all_badges = [
        {"type": "first_lesson", "name": "First Steps", "description": "Complete your first lesson"},
        {"type": "first_quiz", "name": "Quiz Master", "description": "Pass your first quiz"},
        {"type": "beginner_complete", "name": "Beginner Graduate", "description": "Complete all Beginner lessons"},
        {"type": "intermediate_complete", "name": "Intermediate Graduate", "description": "Complete all Intermediate lessons"},
        {"type": "advanced_complete", "name": "Expert Trader", "description": "Complete all Advanced lessons"},
        {"type": "perfect_quiz", "name": "Perfectionist", "description": "Get 100% on any quiz"},
        {"type": "streak_7", "name": "Weekly Warrior", "description": "7 day learning streak"},
        {"type": "streak_30", "name": "Monthly Master", "description": "30 day learning streak"}
    ]
    
    earned_types = {b['badge_type'] for b in badges}
    
    return {
        "earned": [dict(b) for b in badges],
        "available": [b for b in all_badges if b['type'] not in earned_types],
        "total_earned": len(badges),
        "total_available": len(all_badges)
    }

@router.post("/badges/check")
async def check_and_award_badges(user_id: int):
    """Check and award any new badges"""
    awarded = []
    
    # Check first lesson badge
    first_lesson_query = """
        SELECT COUNT(*) as count FROM user_learning_progress
        WHERE user_id = :user_id AND completed = TRUE
    """
    result = await database.fetch_one(first_lesson_query, {"user_id": user_id})
    if result and result['count'] > 0:
        badge = await award_badge(user_id, "first_lesson")
        if badge:
            awarded.append(badge)
    
    # Check beginner complete
    beginner_query = """
        SELECT COUNT(lls.id) as total,
               COUNT(ulp.lesson_id) as completed
        FROM learning_lessons lls
        JOIN learning_modules lm ON lm.id = lls.module_id
        JOIN learning_levels ll ON ll.id = lm.level_id
        LEFT JOIN user_learning_progress ulp 
            ON ulp.lesson_id = lls.id AND ulp.user_id = :user_id AND ulp.completed = TRUE
        WHERE ll.name = 'Beginner'
    """
    result = await database.fetch_one(beginner_query, {"user_id": user_id})
    if result and result['total'] > 0 and result['total'] == result['completed']:
        badge = await award_badge(user_id, "beginner_complete")
        if badge:
            awarded.append(badge)
    
    return {"awarded": awarded}

async def award_badge(user_id: int, badge_type: str):
    """Award a badge if not already earned"""
    try:
        query = """
            INSERT INTO user_badges (user_id, badge_type)
            VALUES (:user_id, :badge_type)
            ON CONFLICT (user_id, badge_type) DO NOTHING
            RETURNING *
        """
        result = await database.fetch_one(query, {
            "user_id": user_id,
            "badge_type": badge_type
        })
        return dict(result) if result else None
    except:
        return None

@router.get("/mentor/guide/{level_id}")
async def get_mentor_guide(level_id: int, user_id: int):
    """Get AI mentor guide for level"""
    # Get user's weak topics from quiz results
    weak_topics_query = """
        SELECT topic_slug, COUNT(*) as error_count
        FROM user_quiz_results uqr
        JOIN lesson_quizzes lq ON lq.id = uqr.question_id
        WHERE uqr.user_id = :user_id AND uqr.is_correct = FALSE
        GROUP BY topic_slug
        ORDER BY error_count DESC
        LIMIT 3
    """
    weak_topics = await database.fetch_all(weak_topics_query, {"user_id": user_id})
    
    # Get level info
    level_query = "SELECT * FROM learning_levels WHERE id = :level_id"
    level = await database.fetch_one(level_query, {"level_id": level_id})
    
    guides = {
        1: {
            "title": "Beginner Foundation",
            "focus": "Master the basics before moving forward",
            "tips": [
                "Start with EUR/USD only—master one pair before diversifying",
                "Always use a stop loss—no exceptions",
                "Risk no more than 1-2% per trade",
                "Focus on process, not profits",
                "Complete every quiz to reinforce learning"
            ],
            "common_mistakes": [
                "Overtrading during quiet hours",
                "Using too much leverage",
                "Ignoring the spread in calculations",
                "Trading without a plan"
            ]
        },
        2: {
            "title": "Intermediate Strategy",
            "focus": "Build your edge with technical analysis",
            "tips": [
                "Always check higher timeframe trend first",
                "Wait for confluence: Support + Pattern + Candlestick",
                "Keep a trading journal—every trade, every emotion",
                "Backtest your strategy for at least 100 trades",
                "Master one strategy before adding others"
            ],
            "common_mistakes": [
                "Taking every setup without filtering",
                "Ignoring correlation between pairs",
                "Changing strategy after 3 losses",
                "Trading during high-impact news without preparation"
            ]
        },
        3: {
            "title": "Advanced Mastery",
            "focus": "Trade like an institution",
            "tips": [
                "Understand liquidity pools and stop hunts",
                "Trade with smart money, not against it",
                "Focus on risk-adjusted returns, not just profits",
                "Build systems, not just strategies",
                "Mental toughness separates professionals from amateurs"
            ],
            "common_mistakes": [
                "Overcomplicating analysis with too many indicators",
                "Neglecting portfolio correlation risk",
                "Increasing size after wins (overconfidence)",
                "Skipping the daily review process"
            ]
        }
    }
    
    guide = guides.get(level_id, guides[1])
    
    return {
        "level": dict(level) if level else None,
        "guide": guide,
        "weak_topics": [dict(t) for t in weak_topics],
        "recommended_focus": [t['topic_slug'] for t in weak_topics] if weak_topics else []
    }

@router.get("/profile/{user_id}")
async def get_learning_profile(user_id: int):
    """Get user's learning profile"""
    query = """
        SELECT * FROM user_learning_profile
        WHERE user_id = :user_id
    """
    profile = await database.fetch_one(query, {"user_id": user_id})
    
    if not profile:
        # Create profile
        insert_query = """
            INSERT INTO user_learning_profile (user_id, first_academy_visit)
            VALUES (:user_id, TRUE)
            RETURNING *
        """
        profile = await database.fetch_one(insert_query, {"user_id": user_id})
    
    return dict(profile) if profile else {"user_id": user_id, "first_academy_visit": True}

@router.post("/profile/{user_id}/visit")
async def mark_academy_visited(user_id: int):
    """Mark that user has visited academy (first time flag)"""
    query = """
        UPDATE user_learning_profile
        SET first_academy_visit = FALSE, last_updated = NOW()
        WHERE user_id = :user_id
    """
    await database.execute(query, {"user_id": user_id})
    return {"visited": True}
