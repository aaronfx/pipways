"""
AI Trading Mentor - PLATFORM INTELLIGENCE SYSTEM v3.0
Central AI brain with contextual access to all platform modules
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timedelta
import os
import httpx
import asyncio
import json

from .security import get_current_user, get_user_id as _user_id
from .database import database  # needed for persistent history

router = APIRouter()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── Persistent conversation history helpers ───────────────────────────────────
# Replaces the in-memory defaultdict(list) which reset on every deploy.
# History is stored in ai_mentor_logs (role + message columns added by migration).

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
        # Reverse so oldest first (DESC gives us newest first)
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
# MODELS
# ==========================================

class MentorQuery(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = Field(None, max_length=1000)
    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    topic: Optional[str] = None
    include_platform_context: bool = True

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class Recommendation(BaseModel):
    type: Literal["course", "blog", "signal", "strategy", "warning"]
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MentorResponse(BaseModel):
    response: str
    recommendations: List[Recommendation]
    context_used: Dict[str, Any]
    command_triggered: Optional[str] = None
    confidence: float = Field(default=0.9, ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserContext(BaseModel):
    journal_performance: Optional[Dict[str, Any]] = None
    last_chart_analysis: Optional[Dict[str, Any]] = None
    active_signals: List[Dict[str, Any]] = []
    available_courses: List[Dict[str, Any]] = []
    recent_blogs: List[Dict[str, Any]] = []
    trading_stats: Optional[Dict[str, Any]] = None
    user_skill_level: str = "intermediate"

class CoachInsights(BaseModel):
    trading_personality: str
    strengths: List[str]
    weaknesses: List[str]
    risk_profile: str
    discipline_score: int
    consistency_score: int
    recommended_next_steps: List[str]
    recommended_resources: List[Recommendation]

# ==========================================
# CONTEXT ENGINE
# ==========================================

async def fetch_journal_performance(client: httpx.AsyncClient, token: str, base_url: str) -> Optional[Dict]:
    """Fetch user trading journal performance"""
    try:
        url = f"{base_url}/ai/performance/dashboard"
        print(f"[FETCH] Calling {url}", flush=True)
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        print(f"[FETCH] Journal response status: {resp.status_code}", flush=True)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[FETCH] Journal data keys: {list(data.keys()) if data else 'empty'}", flush=True)
            return data
        else:
            print(f"[FETCH] Journal error: {resp.text[:200]}", flush=True)
    except Exception as e:
        print(f"[CONTEXT] Journal fetch error: {e}", flush=True)
    return None

async def fetch_active_signals(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    """Fetch active trading signals"""
    try:
        resp = await client.get(
            f"{base_url}/signals/active",
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("signals", [])
    except Exception as e:
        print(f"[CONTEXT] Signals fetch error: {e}", flush=True)
    return []

async def fetch_courses(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    """Fetch available courses"""
    try:
        resp = await client.get(
            f"{base_url}/courses/list",
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("courses", [])
    except Exception as e:
        print(f"[CONTEXT] Courses fetch error: {e}", flush=True)
    return []

async def fetch_blog_posts(client: httpx.AsyncClient, base_url: str) -> List[Dict]:
    """Fetch recent blog posts"""
    try:
        resp = await client.get(
            f"{base_url}/blog/posts",
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            posts = data if isinstance(data, list) else data.get("posts", [])
            return posts[:5]  # Only recent 5
    except Exception as e:
        print(f"[CONTEXT] Blog fetch error: {e}", flush=True)
    return []

async def fetch_last_chart_analysis(client: httpx.AsyncClient, token: str, base_url: str) -> Optional[Dict]:
    """Fetch user's last chart analysis (simulated via session or cache)"""
    # In production, this would query a cache/DB for last analysis
    # For now, return None to allow AI to respond generically
    return None

async def get_user_trading_context(client: httpx.AsyncClient, token: str, user_id: str, base_url: str) -> UserContext:
    """
    Gather comprehensive user context from all platform modules
    Parallel async fetching for performance
    """
    print(f"[CONTEXT] Fetching for user {user_id} from {base_url}", flush=True)

    journal_task = fetch_journal_performance(client, token, base_url)
    signals_task = fetch_active_signals(client, base_url)
    courses_task = fetch_courses(client, base_url)
    blogs_task = fetch_blog_posts(client, base_url)
    chart_task = fetch_last_chart_analysis(client, token, base_url)

    try:
        journal, signals, courses, blogs, chart = await asyncio.gather(
            journal_task, signals_task, courses_task, blogs_task, chart_task,
            return_exceptions=True
        )

        # Log results
        if isinstance(journal, Exception):
            print(f"[CONTEXT] Journal fetch failed: {journal}", flush=True)
            journal = None
        else:
            print(f"[CONTEXT] Journal fetched successfully: {journal is not None}", flush=True)

        if isinstance(signals, Exception):
            print(f"[CONTEXT] Signals fetch failed: {signals}", flush=True)
            signals = []
        else:
            print(f"[CONTEXT] Signals fetched: {len(signals) if signals else 0}", flush=True)

    except Exception as e:
        print(f"[CONTEXT] Gather failed: {e}", flush=True)
        journal, signals, courses, blogs, chart = None, [], [], [], None

    # Handle exceptions
    journal = None if isinstance(journal, Exception) else journal
    signals = [] if isinstance(signals, Exception) else signals
    courses = [] if isinstance(courses, Exception) else courses
    blogs = [] if isinstance(blogs, Exception) else blogs
    chart = None if isinstance(chart, Exception) else chart

    # Extract trading stats from journal if available
    trading_stats = None
    if journal and isinstance(journal, dict):
        trading_stats = {
            "win_rate": journal.get("win_rate", 0),
            "total_trades": journal.get("total_trades", 0),
            "profit_factor": journal.get("profit_factor", 0),
            "max_drawdown": journal.get("max_drawdown", 0),
            "expectancy": journal.get("expectancy", 0),
            "grade": journal.get("overall_grade", "N/A")
        }

    return UserContext(
        journal_performance=journal,
        last_chart_analysis=chart,
        active_signals=signals,
        available_courses=courses,
        recent_blogs=blogs,
        trading_stats=trading_stats
    )

# ==========================================
# COMMAND PROCESSORS
# ==========================================

async def process_review_trades(context: UserContext) -> str:
    """Process /review-trades command"""
    stats = context.trading_stats
    journal = context.journal_performance

    print(f"[REVIEW] Stats: {stats}, Journal: {journal is not None}", flush=True)

    if not stats and not journal:
        return "I don't see any trading data in your journal yet. Please upload your trading history first so I can analyze your performance."

    # Use journal data directly if stats not parsed
    if not stats and journal:
        stats = {
            "win_rate": journal.get("win_rate", 0),
            "total_trades": journal.get("total_trades", 0),
            "profit_factor": journal.get("profit_factor", 0),
            "max_drawdown": journal.get("max_drawdown", 0),
            "expectancy": journal.get("expectancy", 0),
            "grade": journal.get("overall_grade", "N/A")
        }
        print(f"[REVIEW] Using journal stats: {stats}", flush=True)

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

    for sig in signals[:3]:  # Top 3
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
    return None

# ==========================================
# RECOMMENDATION ENGINE
# ==========================================

def generate_recommendations(
    question: str, 
    context: UserContext, 
    ai_response: str
) -> List[Recommendation]:
    """Generate intelligent recommendations based on context and conversation"""
    recommendations = []
    q_lower = question.lower()

    # Risk management recommendations
    if any(word in q_lower for word in ["risk", "loss", "drawdown", "stop loss"]):
        # Find risk management courses
        for course in context.available_courses:
            if "risk" in course.get("title", "").lower() or "management" in course.get("title", "").lower():
                recommendations.append(Recommendation(
                    type="course",
                    title=course.get("title", "Risk Management Course"),
                    description="Master risk management to protect your capital",
                    metadata={"course_id": course.get("id")}
                ))
                break

        # Find relevant blog posts
        for blog in context.recent_blogs:
            if any(word in blog.get("title", "").lower() for word in ["risk", "loss", "psychology"]):
                recommendations.append(Recommendation(
                    type="blog",
                    title=blog.get("title"),
                    description="Related reading material",
                    metadata={"blog_id": blog.get("id")}
                ))
                break

    # Technical analysis recommendations
    elif any(word in q_lower for word in ["chart", "technical", "pattern", "support", "resistance"]):
        for course in context.available_courses:
            if "technical" in course.get("title", "").lower() or "analysis" in course.get("title", "").lower():
                recommendations.append(Recommendation(
                    type="course",
                    title=course.get("title"),
                    description="Improve your chart reading skills"
                ))
                break

    # Signal recommendations if asking about trades
    elif any(word in q_lower for word in ["trade", "signal", "entry", "buy", "sell"]):
        for sig in context.active_signals[:1]:
            recommendations.append(Recommendation(
                type="signal",
                title=f"{sig.get('symbol')} {sig.get('direction')}",
                description=f"Active signal with {sig.get('confidence', 0)}% confidence",
                metadata=sig
            ))

    # Psychology recommendations
    elif any(word in q_lower for word in ["emotion", "fear", "greed", "psychology", "discipline"]):
        for blog in context.recent_blogs:
            if "psychology" in blog.get("title", "").lower() or "emotion" in blog.get("title", "").lower():
                recommendations.append(Recommendation(
                    type="blog",
                    title=blog.get("title"),
                    description="Trading psychology insights"
                ))
                break

    # Strategy recommendations based on performance
    if context.trading_stats:
        win_rate = context.trading_stats.get("win_rate", 0)
        if win_rate < 40 and not any(r.type == "course" for r in recommendations):
            recommendations.append(Recommendation(
                type="strategy",
                title="Strategy Backtesting Guide",
                description="Your win rate suggests reviewing your strategy rules"
            ))

    return recommendations[:3]  # Max 3 recommendations

# ==========================================
# AI PROMPT ENGINEERING
# ==========================================

def build_system_prompt(context: UserContext, skill_level: str) -> str:
    """Build comprehensive system prompt with user context"""

    prompt = f"""You are the AI Trading Mentor for the Pipways Trading Platform. You are a sophisticated trading coach with access to the user's complete trading profile.

USER PROFILE:
Skill Level: {skill_level}
"""

    # Add trading stats if available
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

    # Add active signals context
    if context.active_signals:
        prompt += "\nACTIVE SIGNALS:\n"
        for sig in context.active_signals[:3]:
            prompt += f"• {sig.get('symbol')} {sig.get('direction')} (Confidence: {sig.get('confidence', 0)}%)\n"

    # Add available education
    if context.available_courses:
        prompt += "\nAVAILABLE COURSES:\n"
        for course in context.available_courses[:3]:
            prompt += f"• {course.get('title')}\n"

    # Add personality insights if available
    if context.journal_performance:
        journal = context.journal_performance
        if "ai_coach" in journal:
            coach = journal["ai_coach"]
            prompt += f"""
PSYCHOLOGICAL PROFILE:
• Discipline Score: {coach.get('discipline_score', 0)}/100
• Risk Management: {coach.get('risk_management_score', 0)}/100
• Main Challenge: {coach.get('main_mistake', 'Unknown')}
"""

    prompt += """
YOUR ROLE:
1. Provide actionable, specific trading advice based on the user's data
2. ALWAYS reference their actual performance data when relevant
3. Recommend specific courses from the available list when appropriate
4. Mention relevant active signals when discussing trade ideas
5. Identify psychological patterns from their trading history
6. Be encouraging but realistic about challenges
7. Keep responses concise (max 3 paragraphs) but information-dense
8. If they ask about performance, cite specific numbers

SPECIAL COMMANDS:
- If the user asks about their last chart, reference chart analysis data
- If they ask "why am I losing", analyze their win rate and drawdown
- If they ask for learning resources, recommend specific courses/blogs

RESPONSE FORMAT:
Provide clear, structured advice. Use bullet points for actionable steps."""

    return prompt

# ==========================================
# MAIN ENDPOINTS
# ==========================================

@router.post("/ask", response_model=MentorResponse)
async def ask_mentor(
    query: MentorQuery,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Advanced AI Mentor with platform-wide context awareness.
    Provides intelligent recommendations from courses, signals, and blogs.
    """
    user_id = _user_id(current_user)

    # Check for special commands
    command = detect_special_command(query.question)

    # Initialize response containers
    context_data = UserContext()
    ai_response = ""
    recommendations = []

    # Gather context if enabled (and not a simple greeting)
    if query.include_platform_context and not query.question.lower() in ["hi", "hello", "hey"]:
        try:
            # Extract token from request headers
            auth_header = request.headers.get("authorization", "")
            token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

            # Determine base URL - use request base URL or environment variable
            base_url = str(request.base_url).rstrip("/")
            if not base_url or base_url == "http://":
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

            print(f"[MENTOR] Gathering context from {base_url} for user {user_id}", flush=True)

            async with httpx.AsyncClient() as client:
                context_data = await get_user_trading_context(client, token, user_id, base_url)

            print(f"[MENTOR] Context gathered: journal={context_data.journal_performance is not None}, signals={len(context_data.active_signals)}", flush=True)
        except Exception as e:
            print(f"[MENTOR] Context gathering failed: {e}", flush=True)

    # Process special commands immediately (before AI call)
    if command == "review-trades":
        ai_response = await process_review_trades(context_data)
        print(f"[MENTOR] Processed /review-trades command", flush=True)
    elif command == "strategy":
        ai_response = await process_strategy_analysis(context_data)
    elif command == "signals":
        ai_response = await process_signals_review(context_data)
    elif command == "help":
        ai_response = """Available commands:
/review-trades - Analyze your trading performance
/strategy - Review your strategy consistency  
/signals - Show best active signals
/help - Show this message

Or ask me anything about trading!"""

    # Only call AI if not a special command OR if command processing returned empty
    if not ai_response:
        # Check OpenRouter configuration
        if not OPENROUTER_CONFIGURED:
            ai_response = generate_fallback_response(query.question, context_data, query.skill_level)
            recommendations = generate_recommendations(query.question, context_data, ai_response)

            return MentorResponse(
                response=ai_response,
                recommendations=recommendations,
                context_used={"fallback": True, "data": context_data.dict()},
                confidence=0.6
            )

        # Load conversation history from database (survives deploys)
        history = await _db_load_history(user_id)

        # Build messages for AI
        messages = [{"role": "system", "content": build_system_prompt(context_data, query.skill_level)}]

        # Add recent history (last 5 exchanges)
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current question with context hint
        user_msg = query.question
        if context_data.trading_stats and "performance" in query.question.lower():
            user_msg += f"\n\n[User Performance Context: Win Rate {context_data.trading_stats.get('win_rate', 0)}%, Grade {context_data.trading_stats.get('grade', 'N/A')}]"

        messages.append({"role": "user", "content": user_msg})

        # Call AI with retry logic
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
                            "max_tokens": 500
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

            except httpx.TimeoutException:
                if attempt == max_retries - 1:
                    ai_response = "I'm taking longer than usual to analyze your data. Please try again in a moment."
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[AI ERROR] Attempt {attempt}: {e}", flush=True)
                if attempt == max_retries - 1:
                    ai_response = generate_fallback_response(query.question, context_data, query.skill_level)

    # Generate recommendations based on AI response and context
    recommendations = generate_recommendations(query.question, context_data, ai_response)

    # Persist conversation to database (survives server restarts & deploys)
    topic = query.question[:100] if query.question else ""
    await _db_save_message(user_id, "user",      query.question, topic)
    await _db_save_message(user_id, "assistant", ai_response,    "")

    return MentorResponse(
        response=ai_response,
        recommendations=recommendations,
        context_used={
            "journal_available": context_data.journal_performance is not None,
            "signals_count": len(context_data.active_signals),
            "courses_count": len(context_data.available_courses),
            "command": command
        },
        command_triggered=command,
        confidence=0.9 if not command else 1.0
    )

@router.get("/insights", response_model=CoachInsights)
async def get_coach_insights(
    current_user = Depends(get_current_user)
):
    """
    Get AI Coach insights for the dashboard display.
    Returns trading personality, strengths, weaknesses, and recommendations.
    """
    # FIXED: SQLAlchemy Row objects need dict() or attribute access, not .get()
    if hasattr(current_user, '_mapping'):
        user_id = str(current_user._mapping.get("id", "anonymous"))
    elif isinstance(current_user, dict):
        user_id = _user_id(current_user)
    else:
        try:
            user_id = str(current_user.id)
        except Exception:
            user_id = "anonymous"

    # Use a safe context with empty defaults — skip internal HTTP call
    # (the dummy_token approach always fails; we have no journal data here)
    context = UserContext()

    # Analyze trading personality
    personality = "Developing Trader"
    strengths = []
    weaknesses = []
    risk_profile = "Moderate"

    if context.trading_stats:
        stats = context.trading_stats
        win_rate = stats.get("win_rate", 0)
        pf = stats.get("profit_factor", 0)
        dd = stats.get("max_drawdown", 0)

        if win_rate > 60 and pf > 2:
            personality = "Disciplined Strategist"
            strengths.append("Excellent risk management")
            strengths.append("Consistent profitability")
            risk_profile = "Conservative"
        elif win_rate > 50:
            personality = "Skilled Technician"
            strengths.append("Good entry timing")
        elif win_rate < 40:
            personality = "Learning Trader"
            weaknesses.append("Entry timing needs improvement")
            weaknesses.append("Risk management review needed")

        if dd > 1000:
            weaknesses.append("High drawdown periods")
            risk_profile = "Aggressive"

        if pf < 1.5:
            weaknesses.append("Profit factor below optimal")
    else:
        personality = "New Trader"
        strengths.append("Fresh perspective")
        weaknesses.append("Need more trading data")

    # Generate next steps
    next_steps = []
    if not context.journal_performance:
        next_steps.append("Upload your trading journal for personalized analysis")
    if not any(s in strengths for s in ["Risk management"]):
        next_steps.append("Complete Risk Management Masterclass")
    if context.active_signals:
        next_steps.append("Review today's active signals")

    # Generate resource recommendations
    resources = []
    if context.available_courses:
        for course in context.available_courses[:2]:
            resources.append(Recommendation(
                type="course",
                title=course.get("title"),
                description=course.get("description", "")[:100]
            ))

    return CoachInsights(
        trading_personality=personality,
        strengths=strengths or ["Enthusiastic learner"],
        weaknesses=weaknesses or ["Building track record"],
        risk_profile=risk_profile,
        discipline_score=context.journal_performance.get("ai_coach", {}).get("discipline_score", 50) if context.journal_performance else 50,
        consistency_score=context.journal_performance.get("risk_consistency_score", 50) if context.journal_performance else 50,
        recommended_next_steps=next_steps,
        recommended_resources=resources
    )

@router.get("/history")
async def get_conversation_history(
    current_user = Depends(get_current_user)
):
    """Retrieve last 10 conversation messages for the user from the database."""
    user_id = str(_user_id(current_user))
    history = await _db_load_history(user_id)
    return {"messages": history, "count": len(history)}

@router.post("/clear-history")
async def clear_history(
    current_user = Depends(get_current_user)
):
    """Clear conversation history from the database."""
    user_id = str(_user_id(current_user))
    await _db_clear_history(user_id)
    return {"status": "cleared"}

def generate_fallback_response(question: str, context: UserContext, skill_level: str) -> str:
    """Generate contextual fallback response when AI is unavailable"""
    q = question.lower()

    if "performance" in q and context.trading_stats:
        return f"Based on your data (Win Rate: {context.trading_stats.get('win_rate', 0)}%), you're showing {'good' if context.trading_stats.get('win_rate', 0) > 50 else 'developing'} progress. Check your detailed analytics in the Journal section."

    elif "risk" in q:
        return "Risk management is crucial. Always use stop losses and risk 1-2% per trade. Check out our Risk Management resources in the Courses section."

    elif "signal" in q and context.active_signals:
        return f"We have {len(context.active_signals)} active signals right now. Head to the Signals tab for detailed entry/exit levels."

    else:
        return "I'm currently in offline mode, but I can see your trading data. For detailed analysis, please try again shortly or check your Journal dashboard for AI insights."

# ==========================================
# BACKWARD COMPATIBILITY
# ==========================================

@router.post("/review-trade")
async def review_trade_endpoint(
    trade: dict,
    current_user = Depends(get_current_user)
):
    """Legacy endpoint - redirects to new system"""
    # This would need Request object, so simplified for now
    return {
        "response": "Please use the main chat interface with /review-trades command",
        "recommendations": [],
        "context_used": {}
    }
