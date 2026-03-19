"""
AI Trading Mentor - PLATFORM INTELLIGENCE SYSTEM v4.1
Central AI brain with contextual access to all platform modules + Trading Academy integration
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timedelta
import os
import httpx
import asyncio
import json
import re

from .security import get_current_user, get_user_id as _user_id
from .database import database

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MAX_HISTORY = 10

# ==========================================
# MODELS (Defined first to avoid NameError)
# ==========================================

class AcademyStructure(BaseModel):
    levels: List[Dict[str, Any]]
    modules: Dict[int, List[Dict[str, Any]]]
    lessons: Dict[int, List[Dict[str, Any]]]

class UserAcademyProgress(BaseModel):
    completed_lessons: List[int]
    current_level: Optional[str]
    completion_rate: float
    summary: List[Dict[str, Any]]

class LessonRecommendation(BaseModel):
    type: Literal["lesson", "course", "blog", "signal", "strategy", "warning"]
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    reason: Literal["recommended", "next_step", "foundational", "remedial"] = "recommended"

class UserContext(BaseModel):
    journal_performance: Optional[Dict[str, Any]] = None
    last_chart_analysis: Optional[Dict[str, Any]] = None
    active_signals: List[Dict[str, Any]] = []
    available_courses: List[Dict[str, Any]] = []
    recent_blogs: List[Dict[str, Any]] = []
    trading_stats: Optional[Dict[str, Any]] = None
    user_skill_level: str = "intermediate"
    academy_structure: Optional[AcademyStructure] = None
    academy_progress: Optional[UserAcademyProgress] = None

class MentorQuery(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = Field(None, max_length=1000)
    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    topic: Optional[str] = None
    include_platform_context: bool = True

class MentorResponse(BaseModel):
    response: str
    recommendations: List[LessonRecommendation]
    context_used: Dict[str, Any]
    command_triggered: Optional[str] = None
    confidence: float = Field(default=0.9, ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    academy_progress: Optional[Dict[str, Any]] = None

class CoachInsights(BaseModel):
    trading_personality: str
    strengths: List[str]
    weaknesses: List[str]
    risk_profile: str
    discipline_score: int
    consistency_score: int
    recommended_next_steps: List[str]
    recommended_resources: List[LessonRecommendation]
    academy_progress: Optional[Dict[str, Any]] = None

# ==========================================
# HISTORY HELPERS
# ==========================================

async def _db_load_history(user_id: str) -> list:
    try:
        rows = await database.fetch_all(
            "SELECT role, message FROM ai_mentor_logs "
            "WHERE user_id = :uid AND message != '' "
            "ORDER BY created_at DESC LIMIT :limit",
            {"uid": int(user_id) if user_id.isdigit() else 0, "limit": MAX_HISTORY * 2}
        )
        return [{"role": r["role"], "content": r["message"]} for r in reversed(rows)]
    except Exception as e:
        print(f"[MENTOR] History load error: {e}", flush=True)
        return []

async def _db_save_message(user_id: str, role: str, content: str, topic: str = "") -> None:
    try:
        uid = int(user_id) if user_id.isdigit() else None
        await database.execute(
            "INSERT INTO ai_mentor_logs (user_id, role, message, question_topic, created_at) "
            "VALUES (:uid, :role, :msg, :topic, NOW())",
            {"uid": uid, "role": role, "msg": content, "topic": topic}
        )
    except Exception as e:
        print(f"[MENTOR] History save error: {e}", flush=True)

# ==========================================
# CONTEXT FETCHERS
# ==========================================

async def fetch_journal_performance(client: httpx.AsyncClient, token: str, base_url: str) -> Optional[Dict]:
    try:
        resp = await client.get(
            f"{base_url}/ai/performance/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[CONTEXT] Journal error: {e}", flush=True)
    return None

async def fetch_active_signals(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    try:
        resp = await client.get(f"{base_url}/signals/active", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("signals", [])
    except Exception as e:
        return []

async def fetch_courses(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    try:
        resp = await client.get(f"{base_url}/courses/list", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("courses", [])
    except Exception:
        return []

async def fetch_blog_posts(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    try:
        resp = await client.get(f"{base_url}/blog/posts", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            posts = data if isinstance(data, list) else data.get("posts", [])
            return posts[:5]
    except Exception:
        return []

async def fetch_academy_structure(client: httpx.AsyncClient, base_url: str, token: str) -> AcademyStructure:
    try:
        levels_resp = await client.get(
            f"{base_url}/learning/levels",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        if levels_resp.status_code != 200:
            return AcademyStructure(levels=[], modules={}, lessons={})

        levels = levels_resp.json()
        modules_map = {}
        lessons_map = {}

        for level in levels:
            level_id = level.get("id")
            mod_resp = await client.get(
                f"{base_url}/learning/modules/{level_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if mod_resp.status_code == 200:
                modules = mod_resp.json()
                modules_map[level_id] = modules

                for module in modules:
                    mod_id = module.get("id")
                    les_resp = await client.get(
                        f"{base_url}/learning/lessons/{mod_id}",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5.0
                    )
                    if les_resp.status_code == 200:
                        lessons_map[mod_id] = les_resp.json()

        return AcademyStructure(levels=levels, modules=modules_map, lessons=lessons_map)
    except Exception as e:
        print(f"[ACADEMY] Structure error: {e}", flush=True)
        return AcademyStructure(levels=[], modules={}, lessons={})

async def fetch_user_academy_progress(client: httpx.AsyncClient, base_url: str, token: str, user_id: str) -> UserAcademyProgress:
    try:
        resp = await client.get(
            f"{base_url}/learning/progress/{user_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        if resp.status_code == 200:
            data = resp.json()
            progress_rows = data.get("progress", [])
            completed_lessons = [p["lesson_id"] for p in progress_rows if p.get("completed")]

            current_level = None
            summary = data.get("summary", [])
            for lvl in summary:
                if lvl.get("percent", 0) < 100:
                    current_level = lvl.get("level_name")
                    break

            return UserAcademyProgress(
                completed_lessons=completed_lessons,
                current_level=current_level or "Beginner",
                completion_rate=data.get("completion_rate", 0),
                summary=summary
            )
    except Exception as e:
        print(f"[ACADEMY] Progress error: {e}", flush=True)

    return UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])

# ==========================================
# RECOMMENDATION ENGINE
# ==========================================

def get_next_lessons(academy_structure: AcademyStructure, progress: UserAcademyProgress, limit: int = 2) -> List[LessonRecommendation]:
    """Find next sequential lessons"""
    recommendations = []
    completed_set = set(progress.completed_lessons)

    sorted_levels = sorted(academy_structure.levels, key=lambda x: x.get("order_index", 0))

    for level in sorted_levels:
        level_id = level.get("id")
        level_name = level.get("name")
        modules = academy_structure.modules.get(level_id, [])
        sorted_modules = sorted(modules, key=lambda x: x.get("order_index", 0))

        for module in sorted_modules:
            mod_id = module.get("id")
            mod_name = module.get("title")
            lessons = academy_structure.lessons.get(mod_id, [])
            sorted_lessons = sorted(lessons, key=lambda x: x.get("order_index", 0))

            for lesson in sorted_lessons:
                lesson_id = lesson.get("id")
                if lesson_id not in completed_set:
                    recommendations.append(LessonRecommendation(
                        type="lesson",
                        title=lesson.get("title"),
                        description=f"{mod_name} • {level_name}",
                        url=f"/academy.html?lesson={lesson_id}",
                        metadata={
                            "lesson_id": lesson_id,
                            "module_id": mod_id,
                            "level_id": level_id,
                            "module_name": mod_name,
                            "level_name": level_name
                        },
                        reason="next_step"
                    ))
                    if len(recommendations) >= limit:
                        return recommendations
    return recommendations

def find_relevant_lessons(question: str, academy_structure: AcademyStructure, progress: UserAcademyProgress) -> List[LessonRecommendation]:
    """Find lessons matching question keywords"""
    recommendations = []
    completed_set = set(progress.completed_lessons)
    q_lower = question.lower()

    topic_keywords = {
        "support": ["support", "resistance", "s/r", "levels"],
        "trend": ["trend", "uptrend", "downtrend"],
        "risk": ["risk", "position size", "lot size", "drawdown"],
        "indicator": ["rsi", "macd", "indicator", "oscillator", "moving average"],
        "pattern": ["pattern", "candlestick", "head and shoulders", "flag"],
        "psychology": ["psychology", "emotion", "fear", "greed", "discipline"],
        "strategy": ["strategy", "system", "trading plan"],
        "fibonacci": ["fibonacci", "fib", "retracement"],
        "structure": ["structure", "bos", "choch", "order block", "liquidity"],
        "foundation": ["foundation", "basics", "beginner", "forex", "intro"],
        "entry": ["entry", "entry point", "setup"],
        "exit": ["exit", "take profit", "tp"]
    }

    matched_topics = []
    for topic, keywords in topic_keywords.items():
        if any(kw in q_lower for kw in keywords):
            matched_topics.append(topic)

    if not matched_topics:
        return []

    for level in academy_structure.levels:
        level_id = level.get("id")
        level_name = level.get("name")
        modules = academy_structure.modules.get(level_id, [])

        for module in modules:
            mod_id = module.get("id")
            mod_name = module.get("title")
            mod_title_lower = mod_name.lower()
            lessons = academy_structure.lessons.get(mod_id, [])

            for lesson in lessons:
                lesson_title_lower = lesson.get("title", "").lower()
                lesson_id = lesson.get("id")

                matches = False
                for topic in matched_topics:
                    if topic in lesson_title_lower or topic in mod_title_lower:
                        matches = True
                        break

                if matches:
                    reason = "recommended"
                    if lesson_id in completed_set:
                        reason = "remedial"

                    recommendations.append(LessonRecommendation(
                        type="lesson",
                        title=lesson.get("title"),
                        description=f"{mod_name} • {level_name}",
                        url=f"/academy.html?lesson={lesson_id}",
                        metadata={
                            "lesson_id": lesson_id,
                            "module_id": mod_id,
                            "level_id": level_id,
                            "completed": lesson_id in completed_set
                        },
                        reason=reason
                    ))

    # Sort: incomplete first, then by level order
    sorted_levels = {lvl["id"]: idx for idx, lvl in enumerate(academy_structure.levels)}
    recommendations.sort(key=lambda x: (x.metadata.get("completed", False), sorted_levels.get(x.metadata.get("level_id"), 999)))

    return recommendations[:3]

def ensure_lesson_recommendation(
    existing_recs: List[LessonRecommendation],
    academy_structure: AcademyStructure,
    progress: UserAcademyProgress,
    question: str
) -> List[LessonRecommendation]:
    """CRITICAL: Always ensure at least one lesson recommendation"""
    lesson_recs = [r for r in existing_recs if r.type == "lesson"]

    if lesson_recs:
        return existing_recs

    # Try relevant lessons
    relevant = find_relevant_lessons(question, academy_structure, progress)
    if relevant:
        return existing_recs + relevant

    # Try next sequential lessons
    next_lessons = get_next_lessons(academy_structure, progress, limit=1)
    if next_lessons:
        return existing_recs + next_lessons

    # Ultimate fallback - first available lesson
    if academy_structure.levels:
        first_level = academy_structure.levels[0]
        modules = academy_structure.modules.get(first_level["id"], [])
        if modules:
            first_mod = modules[0]
            lessons = academy_structure.lessons.get(first_mod["id"], [])
            if lessons:
                first_lesson = lessons[0]
                return existing_recs + [LessonRecommendation(
                    type="lesson",
                    title=first_lesson["title"],
                    description=f"{first_mod['title']} • {first_level['name']}",
                    url=f"/academy.html?lesson={first_lesson['id']}",
                    metadata={"lesson_id": first_lesson["id"]},
                    reason="foundational"
                )]

    # If Academy is completely empty, create a generic pointer
    return existing_recs + [LessonRecommendation(
        type="lesson",
        title="Trading Academy",
        description="Start your learning journey",
        url="/academy.html",
        metadata={},
        reason="foundational"
    )]

def generate_recommendations(
    question: str, 
    context: UserContext, 
    academy_structure: AcademyStructure,
    progress: UserAcademyProgress
) -> List[LessonRecommendation]:
    """Generate lesson recommendations"""
    recommendations = []
    q_lower = question.lower()

    # 1. Find relevant lessons based on keywords
    relevant_lessons = find_relevant_lessons(question, academy_structure, progress)
    recommendations.extend(relevant_lessons)

    # 2. If low completion or no relevant found, add next lessons
    if len([r for r in recommendations if r.type == "lesson"]) < 2:
        next_lessons = get_next_lessons(academy_structure, progress, limit=1)
        for nl in next_lessons:
            if not any(r.metadata.get("lesson_id") == nl.metadata.get("lesson_id") for r in recommendations):
                recommendations.append(nl)

    # 3. ENFORCE: Always at least one lesson
    recommendations = ensure_lesson_recommendation(recommendations, academy_structure, progress, question)

    return recommendations[:3]

# ==========================================
# AI PROMPT ENGINEERING (STRICT VERSION)
# ==========================================

def build_system_prompt(context: UserContext, skill_level: str) -> str:
    """Build strict system prompt that enforces lesson recommendations"""

    prompt = f"""You are the AI Trading Mentor for Pipways. You have ONE job: guide users to specific Trading Academy lessons.

STRICT RULES:
1. Keep responses under 150 words (2-3 short paragraphs MAX)
2. NEVER provide long explanations - instead, reference the specific lesson shown below your response
3. If user asks about a topic, briefly acknowledge it then tell them which lesson to take
4. ALWAYS mention that lesson recommendations appear below your message
5. Be concise, direct, and actionable
6. Do NOT lecture - guide to the lesson instead

USER: {skill_level} level trader"""

    if context.academy_progress:
        prog = context.academy_progress
        prompt += f"\nPROGRESS: {prog.completion_rate}% complete, {len(prog.completed_lessons)} lessons done"

    if context.trading_stats:
        stats = context.trading_stats
        prompt += f"\nSTATS: {stats.get('win_rate', 0)}% win rate, Grade {stats.get('grade', 'N/A')}"

    prompt += """

RESPONSE FORMAT:
[1 sentence acknowledging question]
[1 sentence with specific actionable tip]
[1 sentence directing to the lesson card below]

Example: "Great question about support levels! The key is looking for 2+ touches. I've found the perfect lesson for you below - click the card to learn the full strategy."

REMEMBER: The user will see specific lesson cards below your response. Just guide them there. Do NOT write long explanations."""

    return prompt

# ==========================================
# COMMAND PROCESSORS
# ==========================================

async def process_review_trades(context: UserContext) -> str:
    stats = context.trading_stats
    journal = context.journal_performance

    if not stats and not journal:
        return "I need your trading data to analyze performance. Upload your journal, or check out the Risk Management lesson below to improve your metrics!"

    if not stats and journal:
        stats = {
            "win_rate": journal.get("win_rate", 0),
            "total_trades": journal.get("total_trades", 0),
            "grade": journal.get("overall_grade", "N/A")
        }

    return f"📊 Performance: {stats.get('grade', 'N/A')} grade with {stats.get('win_rate', 0)}% win rate. See the Risk Management lesson below to improve these metrics!"

async def process_strategy_analysis(context: UserContext) -> str:
    return "Strategy analysis requires journal data. Upload your trades or start with the Strategy Building lesson below to learn systematic trading!"

async def process_signals_review(context: UserContext) -> str:
    signals = context.active_signals
    if not signals:
        return "No active signals now. Learn how to generate your own signals - check the Technical Analysis lesson below!"

    sig = signals[0]
    return f"📡 Top signal: {sig.get('symbol')} {sig.get('direction')} ({sig.get('confidence', 0)}% confidence). Learn this strategy in the lesson below!"

def detect_special_command(question: str) -> Optional[str]:
    cmd = question.lower().strip()
    if cmd.startswith("/review"):
        return "review-trades"
    elif cmd.startswith("/strategy"):
        return "strategy"
    elif cmd.startswith("/signals"):
        return "signals"
    elif cmd.startswith("/help"):
        return "help"
    elif cmd.startswith("/next") or cmd.startswith("/continue"):
        return "next-lesson"
    return None

# ==========================================
# MAIN ENDPOINT
# ==========================================

@router.post("/ask", response_model=MentorResponse)
async def ask_mentor(
    query: MentorQuery,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """AI Mentor - always returns lesson recommendations"""
    user_id = _user_id(current_user)

    command = detect_special_command(query.question)
    ai_response = ""

    # Initialize context
    context_data = UserContext(
        academy_structure=AcademyStructure(levels=[], modules={}, lessons={}),
        academy_progress=UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])
    )

    # Gather context
    if query.include_platform_context:
        try:
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
            base_url = str(request.base_url).rstrip("/")
            if not base_url or base_url == "http://":
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

            async with httpx.AsyncClient() as client:
                journal, signals, courses, blogs, academy_structure, academy_progress = await asyncio.gather(
                    fetch_journal_performance(client, token, base_url),
                    fetch_active_signals(client, base_url),
                    fetch_courses(client, base_url),
                    fetch_blog_posts(client, base_url),
                    fetch_academy_structure(client, base_url, token),
                    fetch_user_academy_progress(client, base_url, token, user_id),
                    return_exceptions=True
                )

                if isinstance(journal, Exception): journal = None
                if isinstance(signals, Exception): signals = []
                if isinstance(courses, Exception): courses = []
                if isinstance(blogs, Exception): blogs = []
                if isinstance(academy_structure, Exception): academy_structure = AcademyStructure(levels=[], modules={}, lessons={})
                if isinstance(academy_progress, Exception): academy_progress = UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])

                context_data = UserContext(
                    journal_performance=journal,
                    active_signals=signals,
                    available_courses=courses,
                    recent_blogs=blogs,
                    trading_stats={
                        "win_rate": journal.get("win_rate", 0),
                        "total_trades": journal.get("total_trades", 0),
                        "grade": journal.get("overall_grade", "N/A")
                    } if journal else None,
                    academy_structure=academy_structure,
                    academy_progress=academy_progress
                )
        except Exception as e:
            print(f"[MENTOR] Context error: {e}", flush=True)

    # Process commands
    if command == "review-trades":
        ai_response = await process_review_trades(context_data)
    elif command == "strategy":
        ai_response = await process_strategy_analysis(context_data)
    elif command == "signals":
        ai_response = await process_signals_review(context_data)
    elif command == "next-lesson":
        next_lessons = get_next_lessons(context_data.academy_structure, context_data.academy_progress, limit=1)
        if next_lessons:
            nl = next_lessons[0]
            ai_response = f"📚 Ready to continue? Your next lesson is **{nl.title}**. Click the card below to resume your progress!"
        else:
            ai_response = "🎉 You've completed all lessons! Check back soon for new advanced content."
    elif command == "help":
        ai_response = "I can help you learn trading! Try asking about any topic, or use these commands:\n/next - Continue learning\n/review - See your stats\n/signals - Active trade ideas"

    # Generate recommendations (ALWAYS)
    recommendations = generate_recommendations(
        query.question, context_data,
        context_data.academy_structure, context_data.academy_progress
    )

    # Get AI response if not command
    if not ai_response:
        if not OPENROUTER_CONFIGURED:
            ai_response = generate_fallback_response(query.question, context_data)
        else:
            history = await _db_load_history(user_id)
            messages = [{"role": "system", "content": build_system_prompt(context_data, query.skill_level)}]

            for msg in history[-6:]:  # Last 6 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})

            messages.append({"role": "user", "content": query.question})

            # Call AI
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{OPENROUTER_BASE_URL}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                "HTTP-Referer": "https://pipwaysapp.onrender.com",
                                "X-Title": "Pipways Trading Platform",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": OPENROUTER_MODEL,
                                "messages": messages,
                                "temperature": 0.7,
                                "max_tokens": 250  # Force brevity
                            },
                            timeout=15.0
                        )

                        if response.status_code == 200:
                            data = response.json()
                            ai_response = data["choices"][0]["message"]["content"]
                            # Truncate if still too long
                            if len(ai_response) > 500:
                                ai_response = ai_response[:497] + "..."
                            break
                        elif response.status_code == 429:
                            await asyncio.sleep(1)
                            continue
                        else:
                            raise HTTPException(status_code=503, detail="AI service error")

                except Exception as e:
                    print(f"[AI ERROR] {e}", flush=True)
                    if attempt == max_retries - 1:
                        ai_response = generate_fallback_response(query.question, context_data)

    # Save to history
    await _db_save_message(user_id, "user", query.question, query.question[:50])
    await _db_save_message(user_id, "assistant", ai_response, "")

    return MentorResponse(
        response=ai_response,
        recommendations=recommendations,
        context_used={
            "academy_levels": len(context_data.academy_structure.levels),
            "completed_lessons": len(context_data.academy_progress.completed_lessons) if context_data.academy_progress else 0,
            "command": command
        },
        command_triggered=command,
        confidence=0.95 if command else 0.9,
        academy_progress={
            "completion_rate": context_data.academy_progress.completion_rate if context_data.academy_progress else 0,
            "current_level": context_data.academy_progress.current_level if context_data.academy_progress else "Beginner"
        } if context_data.academy_progress else None
    )

def generate_fallback_response(question: str, context: UserContext) -> str:
    """Short fallback responses"""
    q = question.lower()

    if any(w in q for w in ["support", "resistance"]):
        return "Support and Resistance are key levels where price reverses. Learn the exact strategy in the lesson below! 👇"
    elif any(w in q for w in ["risk", "drawdown"]):
        return "Risk management protects your account. Master the 1-2% rule in the Risk Management lesson below! 👇"
    elif any(w in q for w in ["foundation", "beginner", "forex", "start"]):
        return "Welcome! Start with the Forex Foundations lesson below to build your trading base. Click the card to begin! 👇"
    elif any(w in q for w in ["pattern", "candlestick"]):
        return "Chart patterns reveal market psychology. Learn to read them in the Pattern Recognition lesson below! 👇"
    else:
        return "Great question! I've found the perfect lesson for you below. Click to learn this strategy step-by-step! 👇"

# ==========================================
# OTHER ENDPOINTS
# ==========================================

@router.get("/insights", response_model=CoachInsights)
async def get_coach_insights(request: Request, current_user = Depends(get_current_user)):
    user_id = str(_user_id(current_user))

    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    base_url = str(request.base_url).rstrip("/")
    if not base_url or base_url == "http://":
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

    academy_progress = UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])
    try:
        async with httpx.AsyncClient() as client:
            academy_progress = await fetch_user_academy_progress(client, base_url, token, user_id)
    except:
        pass

    # Get next lesson recommendation
    try:
        async with httpx.AsyncClient() as client:
            academy_structure = await fetch_academy_structure(client, base_url, token)
            next_lessons = get_next_lessons(academy_structure, academy_progress, limit=1)
            recommended_resources = next_lessons if next_lessons else []
    except:
        recommended_resources = []

    personality = "Learning Trader"
    if academy_progress.completion_rate > 50:
        personality = "Dedicated Student"
    elif academy_progress.completion_rate > 80:
        personality = "Trading Scholar"

    next_steps = []
    if academy_progress.completion_rate < 10:
        next_steps.append("Start your first Academy lesson")
    elif academy_progress.completion_rate < 100:
        next_steps.append("Continue to next lesson")
    else:
        next_steps.append("Review advanced concepts")

    return CoachInsights(
        trading_personality=personality,
        strengths=["Learning mindset"],
        weaknesses=["Building experience"],
        risk_profile="Moderate",
        discipline_score=50,
        consistency_score=50,
        recommended_next_steps=next_steps,
        recommended_resources=recommended_resources,
        academy_progress={
            "completion_rate": academy_progress.completion_rate,
            "current_level": academy_progress.current_level
        }
    )

@router.get("/history")
async def get_conversation_history(current_user = Depends(get_current_user)):
    user_id = str(_user_id(current_user))
    history = await _db_load_history(user_id)
    return {"messages": history, "count": len(history)}

@router.post("/clear-history")
async def clear_history(current_user = Depends(get_current_user)):
    user_id = str(_user_id(current_user))
    await _db_clear_history(user_id)
    return {"status": "cleared"}

@router.post("/track-lesson-click")
async def track_lesson_click(
    lesson_id: int,
    action: Literal["start", "complete"],
    current_user = Depends(get_current_user)
):
    user_id = _user_id(current_user)
    print(f"[TRACK] User {user_id} {action} lesson {lesson_id}", flush=True)
    return {"status": "tracked", "lesson_id": lesson_id, "action": action}

# Backward compatibility
@router.post("/review-trade")
async def review_trade_endpoint(trade: dict, current_user = Depends(get_current_user)):
    return {
        "response": "Use /review-trades command in chat",
        "recommendations": [],
        "context_used": {}
    }
