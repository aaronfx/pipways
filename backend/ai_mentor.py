"""
AI Trading Mentor - PLATFORM INTELLIGENCE SYSTEM v4.0
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
from .database import database  # needed for persistent history

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Persistent conversation history helpers ───────────────────────────────────
MAX_HISTORY = 10

async def _db_load_history(user_id: str) -> list:
    """Load last MAX_HISTORY*2 messages for a user from the database."""
    try:
        rows = await database.fetch_all(
            "SELECT role, message FROM ai_mentor_logs "
            "WHERE user_id = :uid AND message != '' "
            "ORDER BY created_at DESC LIMIT :limit",
            {"uid": int(user_id) if user_id.isdigit() else 0,
             "limit": MAX_HISTORY * 2}
        )
        return [{"role": r["role"], "content": r["message"]}
                for r in reversed(rows)]
    except Exception as e:
        print(f"[MENTOR] History load error: {e}", flush=True)
        return []

async def _db_save_message(user_id: str, role: str, content: str, topic: str = "") -> None:
    """Persist a single message to ai_mentor_logs."""
    try:
        uid = int(user_id) if user_id.isdigit() else None
        await database.execute(
            "INSERT INTO ai_mentor_logs (user_id, role, message, question_topic, created_at) "
            "VALUES (:uid, :role, :msg, :topic, NOW())",
            {"uid": uid, "role": role, "msg": content, "topic": topic}
        )
    except Exception as e:
        print(f"[MENTOR] History save error: {e}", flush=True)

async def _db_clear_history(user_id: str) -> None:
    """Delete all stored messages for a user."""
    try:
        uid = int(user_id) if user_id.isdigit() else None
        await database.execute(
            "DELETE FROM ai_mentor_logs WHERE user_id = :uid AND message != ''",
            {"uid": uid}
        )
    except Exception as e:
        print(f"[MENTOR] History clear error: {e}", flush=True)

# ==========================================
# ACADEMY INTEGRATION MODELS
# ==========================================

class AcademyLesson(BaseModel):
    id: int
    title: str
    module_id: int
    module_name: str
    level_id: int
    level_name: str
    order_index: int
    completed: bool = False

class AcademyStructure(BaseModel):
    levels: List[Dict[str, Any]]
    modules: Dict[int, List[Dict[str, Any]]]  # level_id -> modules
    lessons: Dict[int, List[Dict[str, Any]]]  # module_id -> lessons

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

# ==========================================
# CONTEXT ENGINE (Extended with Academy)
# ==========================================

async def fetch_journal_performance(client: httpx.AsyncClient, token: str, base_url: str) -> Optional[Dict]:
    """Fetch user trading journal performance"""
    try:
        url = f"{base_url}/ai/performance/dashboard"
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[CONTEXT] Journal fetch error: {e}", flush=True)
    return None

async def fetch_active_signals(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    """Fetch active trading signals"""
    try:
        resp = await client.get(f"{base_url}/signals/active", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("signals", [])
    except Exception as e:
        print(f"[CONTEXT] Signals fetch error: {e}", flush=True)
    return []

async def fetch_courses(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    """Fetch available courses"""
    try:
        resp = await client.get(f"{base_url}/courses/list", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("courses", [])
    except Exception as e:
        print(f"[CONTEXT] Courses fetch error: {e}", flush=True)
    return []

async def fetch_blog_posts(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    """Fetch recent blog posts"""
    try:
        resp = await client.get(f"{base_url}/blog/posts", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            posts = data if isinstance(data, list) else data.get("posts", [])
            return posts[:5]
    except Exception as e:
        print(f"[CONTEXT] Blog fetch error: {e}", flush=True)
    return []

# ── NEW: Academy Structure Fetching ───────────────────────────────────────────

async def fetch_academy_structure(client: httpx.AsyncClient, base_url: str, token: str) -> AcademyStructure:
    """Fetch full academy hierarchy: levels → modules → lessons"""
    try:
        # Fetch levels
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

        # Fetch modules for each level
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

                # Fetch lessons for each module
                for module in modules:
                    mod_id = module.get("id")
                    les_resp = await client.get(
                        f"{base_url}/learning/lessons/{mod_id}",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5.0
                    )
                    if les_resp.status_code == 200:
                        lessons_map[mod_id] = les_resp.json()

        return AcademyStructure(
            levels=levels,
            modules=modules_map,
            lessons=lessons_map
        )
    except Exception as e:
        print(f"[ACADEMY] Structure fetch error: {e}", flush=True)
        return AcademyStructure(levels=[], modules={}, lessons={})

async def fetch_user_academy_progress(client: httpx.AsyncClient, base_url: str, token: str, user_id: str) -> UserAcademyProgress:
    """Fetch user's learning progress from academy"""
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

            # Determine current level
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
        print(f"[ACADEMY] Progress fetch error: {e}", flush=True)

    return UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])

# ==========================================
# LESSON RECOMMENDATION ENGINE
# ==========================================

def get_next_lessons(academy_structure: AcademyStructure, progress: UserAcademyProgress, limit: int = 2) -> List[LessonRecommendation]:
    """Find the next logical lessons based on progress"""
    recommendations = []
    completed_set = set(progress.completed_lessons)

    # Sort levels by order_index
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
                    # Found next lesson
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
    """Find lessons relevant to the user's question"""
    recommendations = []
    completed_set = set(progress.completed_lessons)
    q_lower = question.lower()

    # Keyword matching map
    topic_keywords = {
        "support": ["support", "resistance", "s/r", "levels"],
        "resistance": ["support", "resistance", "s/r", "levels"],
        "trend": ["trend", "trending", "uptrend", "downtrend"],
        "risk": ["risk", "risk management", "position size", "lot size", "drawdown"],
        "indicator": ["rsi", "macd", "indicator", "oscillator", "moving average"],
        "pattern": ["pattern", "candlestick", "chart pattern", "head and shoulders", "flag"],
        "psychology": ["psychology", "emotion", "fear", "greed", "discipline", "mindset"],
        "strategy": ["strategy", "system", "trading plan", "backtest"],
        "fibonacci": ["fibonacci", "fib", "retracement", "extension"],
        "structure": ["structure", "bos", "choch", "order block", "liquidity"]
    }

    # Determine topics in question
    matched_topics = []
    for topic, keywords in topic_keywords.items():
        if any(kw in q_lower for kw in keywords):
            matched_topics.append(topic)

    if not matched_topics:
        return []

    # Search through lessons for matches
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

                # Check if lesson matches topics
                matches = False
                for topic in matched_topics:
                    if topic in lesson_title_lower or topic in mod_title_lower:
                        matches = True
                        break

                if matches:
                    reason = "recommended"
                    if lesson_id in completed_set:
                        reason = "remedial"  # Review completed lesson

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

    # Prioritize incomplete lessons, then by level order
    sorted_levels = {lvl["id"]: idx for idx, lvl in enumerate(academy_structure.levels)}
    recommendations.sort(key=lambda x: (
        x.metadata.get("completed", False),
        sorted_levels.get(x.metadata.get("level_id"), 999)
    ))

    return recommendations[:3]

def ensure_lesson_recommendation(
    existing_recs: List[LessonRecommendation],
    academy_structure: AcademyStructure,
    progress: UserAcademyProgress,
    question: str
) -> List[LessonRecommendation]:
    """CRITICAL: Ensure at least one lesson is always recommended"""
    # Filter existing lesson recommendations
    lesson_recs = [r for r in existing_recs if r.type == "lesson"]

    if lesson_recs:
        return existing_recs

    # Try relevant lessons first
    relevant = find_relevant_lessons(question, academy_structure, progress)
    if relevant:
        return existing_recs + relevant

    # Fall back to next lessons
    next_lessons = get_next_lessons(academy_structure, progress, limit=1)
    if next_lessons:
        return existing_recs + next_lessons

    # Ultimate fallback: first lesson of first module of first level
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

    return existing_recs

# ==========================================
# COMMAND PROCESSORS
# ==========================================

async def process_review_trades(context: UserContext) -> str:
    """Process /review-trades command"""
    stats = context.trading_stats
    journal = context.journal_performance

    if not stats and not journal:
        return "I don't see any trading data in your journal yet. Please upload your trading history first so I can analyze your performance."

    if not stats and journal:
        stats = {
            "win_rate": journal.get("win_rate", 0),
            "total_trades": journal.get("total_trades", 0),
            "profit_factor": journal.get("profit_factor", 0),
            "max_drawdown": journal.get("max_drawdown", 0),
            "expectancy": journal.get("expectancy", 0),
            "grade": journal.get("overall_grade", "N/A")
        }

    win_rate = stats.get("win_rate", 0)
    grade = stats.get("grade", "N/A")
    total = stats.get("total_trades", 0)

    analysis = f"📊 **Performance Review** ({total} trades analyzed)\n\n"
    analysis += f"**Overall Grade:** {grade}\n"
    analysis += f"**Win Rate:** {win_rate}%\n"

    if win_rate < 40:
        analysis += "\n⚠️ **Observation:** Your win rate is below average. This could indicate issues with entry timing or risk management."
    elif win_rate > 60:
        analysis += "\n✅ **Strength:** Excellent win rate! You're good at picking entries."
    else:
        analysis += "\n📈 **Status:** Your win rate is within normal ranges (40-60%)."

    if stats.get("profit_factor", 0) < 1.5:
        analysis += "\n💡 **Tip:** Your profit factor suggests you might be letting losses run too long or cutting winners too early."

    return analysis

async def process_strategy_analysis(context: UserContext) -> str:
    """Process /strategy command"""
    journal = context.journal_performance
    if not journal:
        return "Please upload your trading journal first so I can analyze your strategy patterns."

    strategy = journal.get("detected_strategy", "Unknown")
    consistency = journal.get("risk_consistency_score", 0)

    response = f"🎯 **Strategy Analysis**\n\n"
    response += f"**Detected Strategy:** {strategy}\n"
    response += f"**Risk Consistency:** {consistency}%\n\n"

    if consistency > 80:
        response += "✅ **Strength:** Excellent risk consistency! You maintain disciplined position sizing."
    elif consistency < 50:
        response += "⚠️ **Issue:** Inconsistent risk sizing detected. Try to risk 1-2% per trade consistently."

    response += "\n💡 **Recommendation:** Review your trade journal to see if you're following your strategy rules consistently."
    return response

async def process_signals_review(context: UserContext) -> str:
    """Process /signals command"""
    signals = context.active_signals
    if not signals:
        return "No active signals available right now. Check back later or set up alerts for your favorite pairs."

    response = "📡 **Active Trading Signals**\n\n"
    best_signal = None
    best_score = 0

    for sig in signals[:3]:
        symbol = sig.get("symbol", "N/A")
        direction = sig.get("direction", "N/A")
        conf = sig.get("confidence", 0)
        response += f"• **{symbol}** - {direction} (Confidence: {conf}%)\n"
        if conf > best_score:
            best_score = conf
            best_signal = sig

    if best_signal:
        response += f"\n⭐ **Top Pick:** {best_signal['symbol']} {best_signal['direction']} with {best_score}% confidence"
        response += f"\n   Entry: {best_signal.get('entry_price', 'N/A')} | SL: {best_signal.get('stop_loss', 'N/A')} | TP: {best_signal.get('take_profit', 'N/A')}"

    return response

def detect_special_command(question: str) -> Optional[str]:
    """Detect special commands in user input"""
    cmd = question.lower().strip()
    if cmd.startswith("/review-trades") or cmd.startswith("/review"):
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
# RECOMMENDATION ENGINE (Enhanced)
# ==========================================

def generate_recommendations(
    question: str, 
    context: UserContext, 
    ai_response: str,
    academy_structure: AcademyStructure,
    progress: UserAcademyProgress
) -> List[LessonRecommendation]:
    """Generate intelligent recommendations including Academy lessons"""
    recommendations = []
    q_lower = question.lower()

    # 1. Find relevant lessons based on question content
    relevant_lessons = find_relevant_lessons(question, academy_structure, progress)
    recommendations.extend(relevant_lessons)

    # 2. If no relevant lessons or user is new, get next lessons
    if not recommendations or progress.completion_rate < 10:
        next_lessons = get_next_lessons(academy_structure, progress, limit=1)
        for nl in next_lessons:
            if not any(r.metadata.get("lesson_id") == nl.metadata.get("lesson_id") for r in recommendations):
                recommendations.append(nl)

    # 3. Topic-based recommendations
    if any(word in q_lower for word in ["risk", "loss", "drawdown", "stop loss"]):
        for course in context.available_courses:
            if "risk" in course.get("title", "").lower():
                recommendations.append(LessonRecommendation(
                    type="course",
                    title=course.get("title", "Risk Management Course"),
                    description="Master risk management to protect your capital",
                    metadata={"course_id": course.get("id")}
                ))
                break

    elif any(word in q_lower for word in ["chart", "technical", "pattern", "support", "resistance"]):
        for course in context.available_courses:
            if "technical" in course.get("title", "").lower():
                recommendations.append(LessonRecommendation(
                    type="course",
                    title=course.get("title"),
                    description="Improve your chart reading skills"
                ))
                break

    elif any(word in q_lower for word in ["emotion", "fear", "greed", "psychology", "discipline"]):
        for blog in context.recent_blogs:
            if "psychology" in blog.get("title", "").lower():
                recommendations.append(LessonRecommendation(
                    type="blog",
                    title=blog.get("title"),
                    description="Trading psychology insights"
                ))
                break

    # 4. Performance-based recommendations
    if context.trading_stats:
        win_rate = context.trading_stats.get("win_rate", 0)
        if win_rate < 40:
            recommendations.append(LessonRecommendation(
                type="strategy",
                title="Strategy Backtesting Guide",
                description="Your win rate suggests reviewing your strategy rules"
            ))

    # 5. CRITICAL: Ensure at least one lesson recommendation
    recommendations = ensure_lesson_recommendation(recommendations, academy_structure, progress, question)

    return recommendations[:4]  # Max 4 recommendations

# ==========================================
# AI PROMPT ENGINEERING (Academy-Enhanced)
# ==========================================

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

def build_system_prompt(context: UserContext, skill_level: str) -> str:
    """Build comprehensive system prompt with Academy integration"""

    prompt = f"""You are the AI Trading Mentor for the Pipways Trading Platform. You are a sophisticated trading coach with access to the user's complete trading profile and learning progress.

USER PROFILE:
Skill Level: {skill_level}
"""

    # Add trading stats
    if context.trading_stats:
        stats = context.trading_stats
        prompt += f"""
TRADING PERFORMANCE:
• Total Trades: {stats.get('total_trades', 0)}
• Win Rate: {stats.get('win_rate', 0)}%
• Profit Factor: {stats.get('profit_factor', 0)}
• Max Drawdown: ${stats.get('max_drawdown', 0)}
• Overall Grade: {stats.get('grade', 'N/A')}
"""

    # Add Academy progress
    if context.academy_progress:
        prog = context.academy_progress
        prompt += f"""
LEARNING PROGRESS:
• Completion Rate: {prog.completion_rate}%
• Current Level: {prog.current_level}
• Completed Lessons: {len(prog.completed_lessons)}
"""

    # Add active signals
    if context.active_signals:
        prompt += "\nACTIVE SIGNALS:\n"
        for sig in context.active_signals[:3]:
            prompt += f"• {sig.get('symbol')} {sig.get('direction')} (Confidence: {sig.get('confidence', 0)}%)\n"

    prompt += """
YOUR ROLE AS AI TRADING MENTOR AND LEARNING GUIDE:

1. Provide actionable, specific trading advice based on the user's data
2. ALWAYS reference their actual performance data when relevant
3. GUIDE USERS THROUGH THE TRADING ACADEMY — always recommend the next lesson or relevant lesson
4. If they ask a question covered in the Academy, reference the specific lesson
5. Track their learning progress and encourage continuation
6. If they are struggling with basics, redirect to foundational lessons
7. If they are advanced, suggest intermediate/advanced content
8. Be encouraging but realistic about challenges
9. Keep responses concise (max 3 paragraphs) but information-dense

ACADEMY INTEGRATION RULES:
• After EVERY response, recommend at least one specific Academy lesson
• If user is learning sequentially → suggest the NEXT lesson
• If user is confused about a topic → suggest the relevant foundational lesson
• If user has gaps → suggest remedial lessons
• Never overwhelm — guide step-by-step
• Reference lesson titles specifically

RESPONSE FORMAT:
Provide clear, structured advice. Use bullet points for actionable steps. Always end with a learning recommendation."""

    return prompt

# ==========================================
# MAIN ENDPOINTS (Enhanced)
# ==========================================

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

@router.post("/ask", response_model=MentorResponse)
async def ask_mentor(
    query: MentorQuery,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Advanced AI Mentor with platform-wide context + Trading Academy integration.
    ALWAYS returns at least one lesson recommendation.
    """
    user_id = _user_id(current_user)

    command = detect_special_command(query.question)
    ai_response = ""

    # Initialize context
    context_data = UserContext(
        academy_structure=AcademyStructure(levels=[], modules={}, lessons={}),
        academy_progress=UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])
    )

    # Gather all context including Academy
    if query.include_platform_context:
        try:
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
            base_url = str(request.base_url).rstrip("/")
            if not base_url or base_url == "http://":
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

            async with httpx.AsyncClient() as client:
                # Fetch all context in parallel
                journal_task = fetch_journal_performance(client, token, base_url)
                signals_task = fetch_active_signals(client, base_url)
                courses_task = fetch_courses(client, base_url)
                blogs_task = fetch_blog_posts(client, base_url)
                academy_structure_task = fetch_academy_structure(client, base_url, token)
                academy_progress_task = fetch_user_academy_progress(client, base_url, token, user_id)

                journal, signals, courses, blogs, academy_structure, academy_progress = await asyncio.gather(
                    journal_task, signals_task, courses_task, blogs_task,
                    academy_structure_task, academy_progress_task,
                    return_exceptions=True
                )

                # Handle exceptions
                if isinstance(journal, Exception): journal = None
                if isinstance(signals, Exception): signals = []
                if isinstance(courses, Exception): courses = []
                if isinstance(blogs, Exception): blogs = []
                if isinstance(academy_structure, Exception): academy_structure = AcademyStructure(levels=[], modules={}, lessons={})
                if isinstance(academy_progress, Exception): academy_progress = UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])

                # Build context
                context_data = UserContext(
                    journal_performance=journal,
                    active_signals=signals,
                    available_courses=courses,
                    recent_blogs=blogs,
                    trading_stats={
                        "win_rate": journal.get("win_rate", 0),
                        "total_trades": journal.get("total_trades", 0),
                        "profit_factor": journal.get("profit_factor", 0),
                        "max_drawdown": journal.get("max_drawdown", 0),
                        "grade": journal.get("overall_grade", "N/A")
                    } if journal else None,
                    academy_structure=academy_structure,
                    academy_progress=academy_progress
                )

        except Exception as e:
            print(f"[MENTOR] Context gathering failed: {e}", flush=True)

    # Process special commands
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
            ai_response = f"📚 **Continue Your Learning**\n\nYour next lesson is: **{nl.title}**\n\nThis lesson covers {nl.description}. Click the card below to continue your progress!"
        else:
            ai_response = "🎉 Congratulations! You've completed all available lessons in the Academy. Check back soon for new content!"
    elif command == "help":
        ai_response = """Available commands:
/review-trades - Analyze your trading performance
/strategy - Review your strategy consistency  
/signals - Show best active signals
/next or /continue - Get your next Academy lesson
/help - Show this message

Or ask me anything about trading! I'll always guide you to relevant Academy lessons."""

    # Generate recommendations (ALWAYS includes lessons)
    recommendations = generate_recommendations(
        query.question, context_data, ai_response,
        context_data.academy_structure, context_data.academy_progress
    )

    # Call AI if not a special command
    if not ai_response:
        if not OPENROUTER_CONFIGURED:
            ai_response = generate_fallback_response(query.question, context_data, query.skill_level)
        else:
            history = await _db_load_history(user_id)
            messages = [{"role": "system", "content": build_system_prompt(context_data, query.skill_level)}]

            for msg in history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Add Academy context hint
            user_msg = query.question
            if context_data.academy_progress and context_data.academy_progress.completion_rate < 20:
                user_msg += "\n\n[Note: This user is new to the Academy. Suggest foundational lessons.]"

            messages.append({"role": "user", "content": user_msg})

            # Call AI with retry
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
                                "max_tokens": 600
                            },
                            timeout=15.0
                        )

                        if response.status_code == 200:
                            data = response.json()
                            ai_response = data["choices"][0]["message"]["content"]
                            break
                        elif response.status_code == 429:
                            await asyncio.sleep(1)
                            continue
                        else:
                            raise HTTPException(status_code=503, detail="AI service error")

                except Exception as e:
                    print(f"[AI ERROR] Attempt {attempt}: {e}", flush=True)
                    if attempt == max_retries - 1:
                        ai_response = generate_fallback_response(query.question, context_data, query.skill_level)

    # Persist conversation
    topic = query.question[:100] if query.question else ""
    await _db_save_message(user_id, "user", query.question, topic)
    await _db_save_message(user_id, "assistant", ai_response, "")

    return MentorResponse(
        response=ai_response,
        recommendations=recommendations,
        context_used={
            "journal_available": context_data.journal_performance is not None,
            "signals_count": len(context_data.active_signals),
            "courses_count": len(context_data.available_courses),
            "academy_levels": len(context_data.academy_structure.levels),
            "completed_lessons": len(context_data.academy_progress.completed_lessons) if context_data.academy_progress else 0,
            "command": command
        },
        command_triggered=command,
        confidence=0.9 if not command else 1.0,
        academy_progress={
            "completion_rate": context_data.academy_progress.completion_rate if context_data.academy_progress else 0,
            "current_level": context_data.academy_progress.current_level if context_data.academy_progress else "Beginner",
            "completed_count": len(context_data.academy_progress.completed_lessons) if context_data.academy_progress else 0
        } if context_data.academy_progress else None
    )

# ==========================================
# ADDITIONAL ENDPOINTS
# ==========================================

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

@router.get("/insights", response_model=CoachInsights)
async def get_coach_insights(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Get AI Coach insights including Academy progress"""
    if hasattr(current_user, '_mapping'):
        user_id = str(current_user._mapping.get("id", "anonymous"))
    elif isinstance(current_user, dict):
        user_id = _user_id(current_user)
    else:
        try:
            user_id = str(current_user.id)
        except Exception:
            user_id = "anonymous"

    # Fetch Academy progress
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    base_url = str(request.base_url).rstrip("/")
    if not base_url or base_url == "http://":
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

    academy_progress = None
    try:
        async with httpx.AsyncClient() as client:
            academy_progress = await fetch_user_academy_progress(client, base_url, token, user_id)
    except Exception as e:
        print(f"[INSIGHTS] Academy progress fetch error: {e}", flush=True)
        academy_progress = UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])

    # Generate insights (simplified for demo)
    personality = "Learning Trader"
    if academy_progress and academy_progress.completion_rate > 50:
        personality = "Dedicated Student"

    next_steps = []
    if academy_progress:
        if academy_progress.completion_rate < 10:
            next_steps.append("Start your first Academy lesson")
        elif academy_progress.completion_rate < 50:
            next_steps.append("Continue your Academy progression")
        else:
            next_steps.append("Complete remaining advanced modules")

    return CoachInsights(
        trading_personality=personality,
        strengths=["Enthusiastic learner"],
        weaknesses=["Building track record"],
        risk_profile="Moderate",
        discipline_score=50,
        consistency_score=50,
        recommended_next_steps=next_steps,
        recommended_resources=[],
        academy_progress={
            "completion_rate": academy_progress.completion_rate if academy_progress else 0,
            "current_level": academy_progress.current_level if academy_progress else "Beginner"
        }
    )

@router.get("/history")
async def get_conversation_history(current_user = Depends(get_current_user)):
    """Retrieve last 10 conversation messages"""
    user_id = str(_user_id(current_user))
    history = await _db_load_history(user_id)
    return {"messages": history, "count": len(history)}

@router.post("/clear-history")
async def clear_history(current_user = Depends(get_current_user)):
    """Clear conversation history"""
    user_id = str(_user_id(current_user))
    await _db_clear_history(user_id)
    return {"status": "cleared"}

@router.post("/track-lesson-click")
async def track_lesson_click(
    lesson_id: int,
    action: Literal["start", "complete"],
    current_user = Depends(get_current_user)
):
    """Track when user clicks or completes a lesson from mentor recommendations"""
    user_id = _user_id(current_user)
    try:
        # This would typically update progress via academy_routes
        # For now, log it
        print(f"[MENTOR TRACK] User {user_id} {action} lesson {lesson_id}", flush=True)
        return {"status": "tracked", "lesson_id": lesson_id, "action": action}
    except Exception as e:
        print(f"[MENTOR TRACK] Error: {e}", flush=True)
        return {"status": "error"}

def generate_fallback_response(question: str, context: UserContext, skill_level: str) -> str:
    """Generate contextual fallback response when AI is unavailable"""
    q = question.lower()

    # Check if we have Academy progress to reference
    if context.academy_progress:
        completion = context.academy_progress.completion_rate
        if completion < 10:
            return "Welcome! I'm here to guide your trading journey. Start with the Trading Academy to build a solid foundation. Check the lesson recommendation below!"
        elif completion < 50:
            return f"You're making great progress ({completion}% complete)! Keep learning through the Academy. I've recommended your next lesson below."
        else:
            return "You're an advanced learner! Focus on applying these concepts in your trading journal while completing the remaining Academy modules."

    if "support" in q or "resistance" in q:
        return "Support and Resistance are fundamental concepts. I've found the perfect lesson for you in the Academy — check the recommendation below!"
    elif "risk" in q:
        return "Risk management is crucial. Always use stop losses and risk 1-2% per trade. I've recommended a specific Risk Management lesson for you."
    elif "signal" in q and context.active_signals:
        return f"We have {len(context.active_signals)} active signals right now. Head to the Signals tab for detailed entry/exit levels, or check out the Academy to learn how signals are generated."
    else:
        return "I'm currently in offline mode, but I can see your Academy progress. Check the lesson recommendation below to continue your learning journey!"

# ==========================================
# BACKWARD COMPATIBILITY
# ==========================================

@router.post("/review-trade")
async def review_trade_endpoint(trade: dict, current_user = Depends(get_current_user)):
    """Legacy endpoint - redirects to new system"""
    return {
        "response": "Please use the main chat interface with /review-trades command",
        "recommendations": [],
        "context_used": {}
    }
