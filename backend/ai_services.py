"""
AI Screening & Analysis Services - PRODUCTION READY v2.0
Updated: Integrated Trading Academy lesson recommendations
Fixed: Removed duplicate routes (now in dedicated performance router), cleaned imports
"""
import os
import base64
import json
import httpx
import re
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from .security import get_current_user

router = APIRouter()

# Import performance calculation from performance module
from .performance import calculate_performance_metrics

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = OPENROUTER_API_KEY is not None and OPENROUTER_API_KEY != ""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Common trading symbols pattern
COMMON_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "XAGUSD", 
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "US30", "US100", "DE30"
]

# ==========================================
# ACADEMY INTEGRATION MODELS
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

# ==========================================
# REQUEST MODELS
# ==========================================

class MentorRequest(BaseModel):
    # Accept both 'question' (legacy) and 'message' (new frontend)
    question: Optional[str] = None
    message: Optional[str] = None
    skill_level: str = "intermediate"
    include_platform_context: bool = False

    @property
    def resolved_question(self) -> str:
        """Return whichever field the client sent, preferring message"""
        return (self.message or self.question or "").strip()


class MentorInsightsResponse(BaseModel):
    trading_personality: str = "Developing Trader"
    discipline_score: int = 0
    consistency_score: int = 0
    strengths: List[str] = []
    weaknesses: List[str] = []
    risk_profile: str = "Moderate"
    recommended_next_steps: List[str] = []
    recommended_resources: List[Dict[str, Any]] = []


class TrackLessonRequest(BaseModel):
    lesson_id: str

class TradeValidatorRequest(BaseModel):
    entry_price: float
    stop_loss: float
    take_profit: float
    direction: str  # BUY or SELL
    symbol: Optional[str] = None

class SignalSaveRequest(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    analysis: Optional[str] = None

class ChartAnalyzeRequest(BaseModel):
    """For text-based chart analysis requests"""
    symbol: str
    description: str
    timeframe: Optional[str] = "1H"

# ==========================================
# ACADEMY INTEGRATION HELPERS
# ==========================================

async def fetch_academy_structure(client: httpx.AsyncClient, base_url: str, token: str) -> AcademyStructure:
    """
    Fetch full academy hierarchy: levels → modules → lessons.
    Uses parallel fetching per level to reduce total latency.
    Logs detailed errors so failures are visible in Render logs.
    """
    headers = {"Authorization": f"Bearer {token}"}
    try:
        levels_resp = await client.get(
            f"{base_url}/learning/levels",
            headers=headers,
            timeout=12.0
        )
        if levels_resp.status_code != 200:
            print(f"[ACADEMY] /learning/levels returned {levels_resp.status_code} — empty structure", flush=True)
            return AcademyStructure(levels=[], modules={}, lessons={})

        levels = levels_resp.json()
        if not levels:
            print("[ACADEMY] /learning/levels returned empty list", flush=True)
            return AcademyStructure(levels=[], modules={}, lessons={})

        print(f"[ACADEMY] Fetched {len(levels)} levels", flush=True)
        modules_map = {}
        lessons_map = {}

        # Fetch modules for each level in parallel
        import asyncio as _asyncio

        async def fetch_level_modules(level):
            level_id = level.get("id")
            try:
                mod_resp = await client.get(
                    f"{base_url}/learning/modules/{level_id}",
                    headers=headers,
                    timeout=8.0
                )
                if mod_resp.status_code != 200:
                    print(f"[ACADEMY] modules/{level_id} → {mod_resp.status_code}", flush=True)
                    return level_id, [], {}
                modules = mod_resp.json() or []

                # Fetch lessons for each module in parallel
                local_lessons = {}
                async def fetch_mod_lessons(module):
                    mod_id = module.get("id")
                    try:
                        les_resp = await client.get(
                            f"{base_url}/learning/lessons/{mod_id}",
                            headers=headers,
                            timeout=8.0
                        )
                        if les_resp.status_code == 200:
                            lessons = les_resp.json() or []
                            return mod_id, lessons
                        print(f"[ACADEMY] lessons/{mod_id} → {les_resp.status_code}", flush=True)
                    except Exception as e:
                        print(f"[ACADEMY] lessons/{mod_id} error: {e}", flush=True)
                    return mod_id, []

                lesson_results = await _asyncio.gather(*[fetch_mod_lessons(m) for m in modules])
                for mod_id, lessons in lesson_results:
                    if lessons:
                        local_lessons[mod_id] = lessons

                return level_id, modules, local_lessons
            except Exception as e:
                print(f"[ACADEMY] modules/{level_id} error: {e}", flush=True)
                return level_id, [], {}

        level_results = await _asyncio.gather(*[fetch_level_modules(lv) for lv in levels])
        for level_id, modules, local_lessons in level_results:
            if modules:
                modules_map[level_id] = modules
            lessons_map.update(local_lessons)

        total_lessons = sum(len(v) for v in lessons_map.values())
        print(f"[ACADEMY] Structure loaded: {len(levels)} levels, {len(modules_map)} modules with lessons, {total_lessons} total lessons", flush=True)
        return AcademyStructure(levels=levels, modules=modules_map, lessons=lessons_map)

    except Exception as e:
        print(f"[ACADEMY] Structure fetch failed: {type(e).__name__}: {e}", flush=True)
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
                            "level_id": level_id
                        },
                        reason="next_step"
                    ))
                    if len(recommendations) >= limit:
                        return recommendations
    return recommendations

def _kw_match(text: str, keyword: str) -> bool:
    """
    Word-boundary-aware keyword match.
    Short terms (sma, ema, rsi, etc.) must appear as whole words to prevent
    false positives like 'sma' matching inside 'smart money'.
    """
    import re as _re
    _SHORT = {"sma", "ema", "rsi", "adx", "atr", "fvg", "bos", "ma", "r:r", "s/r", "mtf"}
    if keyword in _SHORT:
        return bool(_re.search(r"(?<![\w])" + _re.escape(keyword) + r"(?![\w])", text))
    return keyword in text


def find_relevant_lessons(question: str, academy_structure: AcademyStructure, progress: UserAcademyProgress) -> List[LessonRecommendation]:
    """
    Two-layer keyword matching against real curriculum lesson titles.
    Layer 1: User question → topic buckets (via question_triggers)
    Layer 2: Topic buckets → lesson title fragments (via lesson_title_map)
    Uses word-boundary matching for short terms to prevent false positives.
    """
    recommendations = []
    completed_set = set(progress.completed_lessons)
    q_lower = question.lower()

    # ── Layer 1: Question keywords → topic buckets ─────────────────────────
    question_triggers = {
        "smc": [
            "smart money", "smc", "order block", "institutional", "imbalance",
            "fair value gap", "fvg", "bos", "choch", "break of structure",
            "change of character", "liquidity sweep", "inducement",
            "buy side", "sell side", "wyckoff",
        ],
        "liquidity": [
            "liquidity", "stop hunt", "equal highs", "equal lows",
            "swept", "sweep", "stop run", "fake out",
        ],
        "support": [
            "support", "resistance", "s/r", "key level", "horizontal level",
            "dynamic support", "dynamic resistance", "supply zone", "demand zone",
        ],
        "trend": [
            "trend", "uptrend", "downtrend", "higher high", "lower low",
            "higher low", "trending", "trendline", "trend line",
        ],
        "risk": [
            "risk management", "position sizing", "position size", "lot size",
            "drawdown", "money management", "stop loss", "risk per trade",
            "how much to risk", "account risk", "portfolio",
        ],
        "rr": [
            "risk reward", "r:r", "rr ratio", "take profit", "reward to risk",
            "risk to reward",
        ],
        "indicator": [
            "indicator", "oscillator", "rsi", "macd", "moving average",
            "ema", "sma", "bollinger", "stochastic", "adx", "atr",
        ],
        "fibonacci": [
            "fibonacci", "fib retracement", "fib level", "fib extension",
            "golden ratio", "0.618", "0.382",
        ],
        "pattern": [
            "chart pattern", "head and shoulders", "double top", "double bottom",
            "flag pattern", "pennant", "wedge", "triangle", "cup and handle",
            "engulfing", "pin bar", "doji", "hammer",
        ],
        "candlestick": [
            "candlestick", "candle reading", "candle wick", "candle body",
            "inside bar", "outside bar", "bullish candle", "bearish candle",
        ],
        "timeframe": [
            "timeframe", "time frame", "h4", "h1", "m15", "daily chart",
            "multi timeframe", "mtf", "trading session", "london session",
            "new york session", "asian session", "best time to trade",
        ],
        "strategy": [
            "trading strategy", "trading plan", "trading system", "backtest",
            "trading rules", "methodology", "trade setup", "my strategy",
        ],
        "performance": [
            "performance", "trade journal", "win rate", "profit factor",
            "expectancy", "tracking trades", "review my trades",
        ],
        "psychology": [
            "psychology", "emotion", "fear", "greed", "discipline",
            "mindset", "revenge trade", "fomo", "overtrading", "patience",
        ],
        "foundation": [
            "what is forex", "how does forex work", "currency pair explained",
            "what is a pip", "what is spread", "what is leverage",
            "how to start trading", "new to forex", "forex for beginners",
        ],
        "confluence": [
            "confluence", "multiple signals", "combine indicators",
            "confirmation signal", "align timeframes",
        ],
    }

    # ── Layer 2: Topic bucket → lesson/module title fragments ──────────────
    # Fragments are substrings of real lesson/module titles from the curriculum.
    lesson_title_map = {
        "smc": [
            "order block", "institutional", "market structure and smart money",
            "liquidity and market structure",
        ],
        "liquidity": [
            "liquidity and market structure", "market structure and smart money",
        ],
        "support": [
            "support and resistance", "dynamic support",
        ],
        "trend": [
            "identifying trend", "trend analysis", "multiple timeframe",
        ],
        "risk": [
            "risk management", "1-2% rule", "stop loss and take profit",
            "position sizing", "advanced risk", "portfolio heat",
        ],
        "rr": [
            "stop loss and take profit", "expectancy", "risk management",
        ],
        "indicator": [
            "momentum indicator", "moving average strategies", "technical indicator",
            "fibonacci",
        ],
        "fibonacci": [
            "fibonacci",
        ],
        "pattern": [
            "chart pattern", "candlestick chart",
        ],
        "candlestick": [
            "candlestick chart", "candlestick",
        ],
        "timeframe": [
            "trading session", "multiple timeframe", "best times to trade",
        ],
        "strategy": [
            "trading system", "backtesting", "creating your trading",
            "trading plan", "complete trading plan",
        ],
        "performance": [
            "performance review", "expectancy", "profit factor", "backtesting",
        ],
        "psychology": [
            "psychology", "trading plan", "performance review",
        ],
        "foundation": [
            "what is forex", "who trades forex", "currency pairs and price",
            "major, minor", "reading pips", "introduction to forex",
        ],
        "confluence": [
            "confluence", "multiple timeframe", "fibonacci and advanced",
        ],
    }

    # ── Match question → topic buckets ─────────────────────────────────────
    matched_topics = []
    for topic, triggers in question_triggers.items():
        if any(_kw_match(q_lower, kw) for kw in triggers):
            matched_topics.append(topic)

    if not matched_topics:
        return []

    # ── Search academy structure for matching lessons ──────────────────────
    for level in academy_structure.levels:
        level_id = level.get("id")
        level_name = level.get("name")
        modules = academy_structure.modules.get(level_id, [])

        for module in modules:
            mod_id = module.get("id")
            mod_name = module.get("title", "")
            mod_title_lower = mod_name.lower()
            lessons = academy_structure.lessons.get(mod_id, [])

            for lesson in lessons:
                lesson_title_lower = lesson.get("title", "").lower()
                lesson_id = lesson.get("id")

                matches = False
                for topic in matched_topics:
                    frags = lesson_title_map.get(topic, [topic])
                    for frag in frags:
                        if frag in lesson_title_lower or frag in mod_title_lower:
                            matches = True
                            break
                    if matches:
                        break

                if matches:
                    reason = "remedial" if lesson_id in completed_set else "recommended"
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

    # Sort: incomplete lessons first, then by curriculum level order
    sorted_levels = {lvl["id"]: idx for idx, lvl in enumerate(academy_structure.levels)}
    recommendations.sort(key=lambda x: (
        x.metadata.get("completed", False),
        sorted_levels.get(x.metadata.get("level_id"), 999)
    ))

    return recommendations[:3]

def generate_lesson_recommendations(
    question: str, 
    academy_structure: AcademyStructure,
    progress: UserAcademyProgress
) -> List[LessonRecommendation]:
    """Generate lesson recommendations - ALWAYS returns at least one"""
    # Try relevant lessons first
    relevant = find_relevant_lessons(question, academy_structure, progress)
    if relevant:
        return relevant

    # Try next sequential lessons
    next_lessons = get_next_lessons(academy_structure, progress, limit=1)
    if next_lessons:
        return next_lessons

    # Ultimate fallback - first available lesson
    if academy_structure.levels:
        first_level = academy_structure.levels[0]
        modules = academy_structure.modules.get(first_level["id"], [])
        if modules:
            first_mod = modules[0]
            lessons = academy_structure.lessons.get(first_mod["id"], [])
            if lessons:
                first_lesson = lessons[0]
                return [LessonRecommendation(
                    type="lesson",
                    title=first_lesson["title"],
                    description=f"{first_mod['title']} • {first_level['name']}",
                    url=f"/academy.html?lesson={first_lesson['id']}",
                    metadata={"lesson_id": first_lesson["id"]},
                    reason="foundational"
                )]

    # Academy structure empty — use static fallback lessons
    # These are the first 3 lessons from the standard Pipways curriculum
    # so users always get a meaningful starting point even when DB fetch fails
    static_fallbacks = [
        LessonRecommendation(
            type="lesson",
            title="What is Forex Trading?",
            description="Introduction to Forex Trading • Beginner",
            url="/academy.html",
            metadata={"lesson_id": None, "static": True},
            reason="foundational"
        ),
        LessonRecommendation(
            type="lesson",
            title="The 1-2% Rule",
            description="Basic Risk Management • Beginner",
            url="/academy.html",
            metadata={"lesson_id": None, "static": True},
            reason="foundational"
        ),
    ]
    # Filter to one and return — keeps recommendation count consistent
    return [static_fallbacks[0]]

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def extract_symbol_from_text(text: str) -> Optional[str]:
    """Extract trading symbol from AI response text"""
    if not text:
        return None

    text_upper = text.upper()

    # Check for common symbols
    for symbol in COMMON_SYMBOLS:
        if symbol in text_upper:
            return symbol

    # Regex pattern for forex pairs (6 chars, 3 letters + 3 letters)
    forex_pattern = r'([A-Z]{3})([A-Z]{3})'
    matches = re.findall(forex_pattern, text_upper)
    if matches:
        return matches[0][0] + matches[0][1]

    # Pattern for crypto (BTC, ETH, etc.)
    crypto_pattern = r'(BTC|ETH|XRP|LTC|BCH|ADA|DOT|LINK)[-/]?(USD|USDT|USDC|EUR)'
    match = re.search(crypto_pattern, text_upper)
    if match:
        return match.group(0).replace("-", "").replace("/", "")

    return None

def calculate_directional_rr(entry: float, sl: float, tp: float, direction: str) -> tuple:
    """
    Calculate direction-aware risk-reward ratio.
    Returns (rr_ratio, risk_reward_text, is_valid_structure)
    """
    direction = direction.upper()

    if direction == "BUY":
        risk = entry - sl
        reward = tp - entry
        is_valid = sl < entry < tp
    elif direction == "SELL":
        risk = sl - entry
        reward = entry - tp
        is_valid = tp < entry < sl
    else:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        is_valid = False

    risk = abs(risk)
    reward = abs(reward)

    rr_ratio = reward / risk if risk > 0 else 0

    # Clamp extreme values
    if rr_ratio > 10:
        rr_ratio = 10

    risk_reward_text = f"1:{rr_ratio:.2f}"

    return rr_ratio, risk_reward_text, is_valid

def calculate_quality_score(structure_valid: bool, rr_ratio: float, structure_quality: str) -> tuple:
    """
    Calculate deterministic trade quality score and grade.
    Returns (score, probability, grade)
    """
    score = 0

    if structure_valid:
        score += 25

    if rr_ratio >= 2:
        score += 25
    if rr_ratio >= 3:
        score += 10

    quality = structure_quality.lower() if structure_quality else ""
    if quality == "excellent":
        score += 20
    elif quality == "good":
        score += 10

    # Cap at 100
    score = min(score, 100)

    # Convert to probability
    probability = score / 100

    # Determine grade
    if score >= 85:
        grade = "A+"
    elif score >= 75:
        grade = "A"
    elif score >= 60:
        grade = "B"
    else:
        grade = "C"

    return score, probability, grade

# ==========================================
# AI MENTOR ENDPOINTS (Updated with Academy)
# ==========================================

@router.post("/mentor/ask")
async def ask_mentor(
    request: MentorRequest,
    req: Request,
    current_user = Depends(get_current_user)
):
    """
    AI Trading Mentor - Provides educational trading guidance with Academy lesson recommendations.
    ALWAYS returns at least one lesson recommendation.
    """
    question = request.resolved_question
    skill_level = request.skill_level

    if not question or len(question) < 2:
        raise HTTPException(400, "Question too short")

    # Gather Academy context
    auth_header = req.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    # Build base URL — req.base_url can return http:// on Render/proxied deployments
    # which causes HTTPS redirects that strip auth headers → 401 → empty academy structure
    raw_base = str(req.base_url).rstrip("/")
    if not raw_base or raw_base in ("http://", "https://"):
        raw_base = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    # Force HTTPS for non-localhost URLs to prevent redirect loops
    if raw_base.startswith("http://") and "localhost" not in raw_base and "127.0.0.1" not in raw_base:
        raw_base = raw_base.replace("http://", "https://", 1)
    base_url = raw_base

    user_id = str(current_user.get("id", "anonymous")) if isinstance(current_user, dict) else str(getattr(current_user, "id", "anonymous"))

    # Fetch Academy data
    academy_structure = AcademyStructure(levels=[], modules={}, lessons={})
    academy_progress = UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])

    try:
        async with httpx.AsyncClient() as client:
            academy_structure, academy_progress = await asyncio.gather(
                fetch_academy_structure(client, base_url, token),
                fetch_user_academy_progress(client, base_url, token, user_id),
                return_exceptions=True
            )
            if isinstance(academy_structure, Exception):
                academy_structure = AcademyStructure(levels=[], modules={}, lessons={})
            if isinstance(academy_progress, Exception):
                academy_progress = UserAcademyProgress(completed_lessons=[], current_level="Beginner", completion_rate=0, summary=[])
    except Exception as e:
        print(f"[MENTOR] Academy fetch error: {e}", flush=True)

    # Generate lesson recommendations (ALWAYS)
    recommendations = generate_lesson_recommendations(question, academy_structure, academy_progress)

    if not OPENROUTER_CONFIGURED:
        # Fallback response - short and lesson-focused
        q_lower = question.lower()
        if any(w in q_lower for w in ["support", "resistance"]):
            response_text = "Support and Resistance are key levels where price reverses. Learn the exact strategy in the lesson below! 👇"
        elif any(w in q_lower for w in ["risk", "drawdown", "loss"]):
            response_text = "Risk management protects your account. Master position sizing in the lesson below! 👇"
        elif any(w in q_lower for w in ["foundation", "beginner", "start", "forex"]):
            response_text = "Welcome! Start with the Forex Foundations lesson below to build your trading base. 👇"
        elif any(w in q_lower for w in ["pattern", "candlestick", "chart"]):
            response_text = "Chart patterns reveal market psychology. Learn to read them in the lesson below! 👇"
        else:
            response_text = "Great question! I've found the perfect lesson for you below. Click to learn this strategy step-by-step! 👇"

        return {
            "response": response_text,
            "recommendations": [rec.dict() for rec in recommendations],
            "suggested_resources": [],
            "mode": "fallback",
            "configured": False,
            "academy_progress": {
                "completion_rate": academy_progress.completion_rate,
                "current_level": academy_progress.current_level
            }
        }

    # Build strict system prompt
    system_prompt = f"""You are the AI Trading Mentor for Pipways. Guide users to specific Trading Academy lessons.

STRICT RULES:
1. Keep responses under 150 words (2-3 short paragraphs MAX)
2. NEVER provide long explanations - reference the specific lesson shown below
3. Briefly acknowledge the question, give one actionable tip, then direct to the lesson
4. ALWAYS mention that lesson recommendations appear below your message
5. Be concise and direct

USER: {skill_level} level | PROGRESS: {academy_progress.completion_rate}% complete

RESPONSE FORMAT:
[1 sentence acknowledging question]
[1 sentence with specific actionable tip] 
[1 sentence directing to lesson card below]

Example: "Great question about support levels! The key is looking for 2+ touches. Click the lesson card below to learn the full strategy!"

REMEMBER: User will see specific lesson cards below your response. Just guide them there."""

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
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": 300,  # Force brevity
                    "temperature": 0.7
                },
                timeout=30.0
            )

            if response.status_code != 200:
                error_text = response.text
                print(f"[AI ERROR] OpenRouter HTTP {response.status_code}: {error_text}", flush=True)

                if response.status_code == 401:
                    raise HTTPException(500, "AI authentication failed. Check API key.")
                elif response.status_code == 429:
                    raise HTTPException(503, "AI service rate limited. Please try again.")
                else:
                    raise HTTPException(503, "AI service temporarily unavailable")

            data = response.json()

            if "choices" not in data or len(data["choices"]) == 0:
                raise HTTPException(500, "Invalid AI response format")

            ai_response = data["choices"][0]["message"]["content"]

            # Truncate if still too long
            if len(ai_response) > 600:
                ai_response = ai_response[:597] + "..."

            return {
                "response": ai_response,
                "recommendations": [rec.dict() for rec in recommendations],
                "suggested_resources": [],
                "mode": "ai",
                "model": OPENROUTER_MODEL,
                "configured": True,
                "academy_progress": {
                    "completion_rate": academy_progress.completion_rate,
                    "current_level": academy_progress.current_level
                }
            }

    except httpx.TimeoutException:
        raise HTTPException(504, "AI request timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI ERROR] Unexpected error: {e}", flush=True)
        # Fallback with recommendations
        return {
            "response": "I'm currently in offline mode, but I've found a great lesson for you below! Check it out to learn more. 👇",
            "recommendations": [rec.dict() for rec in recommendations],
            "suggested_resources": [],
            "mode": "error_fallback",
            "configured": True,
            "academy_progress": {
                "completion_rate": academy_progress.completion_rate,
                "current_level": academy_progress.current_level
            }
        }

@router.post("/mentor/ask-legacy")
async def ask_mentor_legacy(
    question: str = Form(...),
    skill_level: str = Form("intermediate"),
    req: Request = None,
    current_user = Depends(get_current_user)
):
    """Legacy form-data endpoint for compatibility"""
    return await ask_mentor(MentorRequest(question=question, skill_level=skill_level), req, current_user)


# ==========================================
# MENTOR INSIGHTS ENDPOINT
# Dashboard calls GET /ai/mentor/insights
# ==========================================

@router.get("/mentor/insights")
async def get_mentor_insights(
    current_user=Depends(get_current_user)
):
    """
    Returns AI coach insights for the sidebar panel.
    Pulls from any existing performance data for the user.
    Returns sensible defaults when no trade data exists yet.
    """
    user_id = str(current_user.get("id", "")) if isinstance(current_user, dict) else str(getattr(current_user, "id", ""))

    # Default insights — enriched once we have performance data
    return {
        "trading_personality": "Developing Trader",
        "discipline_score": 0,
        "consistency_score": 0,
        "strengths": [
            "Seeking knowledge and improvement",
            "Using AI-powered tools for analysis"
        ],
        "weaknesses": [
            "Upload a trade statement to unlock personalised insights"
        ],
        "risk_profile": "Unknown — import trades to assess",
        "recommended_next_steps": [
            "Import your MT4/MT5 trade history in Performance Analytics",
            "Complete at least one Trading Academy course",
            "Ask the AI Mentor a specific trading question"
        ],
        "recommended_resources": [
            {
                "type": "lesson",
                "title": "What is Forex Trading?",
                "description": "Introduction to Forex Trading • Beginner — the essential first lesson",
                "url": "/academy.html",
                "metadata": {"lesson_id": None, "note": "Open academy to start"}
            },
            {
                "type": "lesson",
                "title": "The 1-2% Rule",
                "description": "Basic Risk Management • Beginner — protect your account from day one",
                "url": "/academy.html",
                "metadata": {"lesson_id": None, "note": "Open academy to find this lesson"}
            }
        ]
    }


# ==========================================
# TRACK LESSON CLICK ENDPOINT
# Dashboard calls POST /ai/mentor/track-lesson-click
# ==========================================

@router.post("/mentor/track-lesson-click")
async def track_lesson_click(
    request: TrackLessonRequest,
    current_user=Depends(get_current_user)
):
    """
    Records when a user clicks a recommended lesson card.
    Lightweight — logs to console for now; extend to DB as needed.
    """
    user_id = str(current_user.get("id", "")) if isinstance(current_user, dict) else str(getattr(current_user, "id", ""))
    lesson_id = request.lesson_id

    print(f"[LESSON CLICK] user={user_id} lesson={lesson_id}", flush=True)

    # TODO: persist to a lesson_clicks table when ready
    # await db.execute("INSERT INTO lesson_clicks (user_id, lesson_id) VALUES ($1, $2)", user_id, lesson_id)

    return {"status": "tracked", "lesson_id": lesson_id}

# ==========================================
# TRADE VALIDATOR ENDPOINTS (Unchanged)
# ==========================================

@router.post("/trade/validate")
async def validate_trade(
    request: TradeValidatorRequest,
    current_user = Depends(get_current_user)
):
    """
    AI Trade Validator - Analyze trade setup quality.
    """
    entry = request.entry_price
    sl = request.stop_loss
    tp = request.take_profit
    direction = request.direction.upper()
    symbol = request.symbol or "Unknown"

    # Calculate direction-aware RR
    rr_ratio, risk_reward_text, is_valid = calculate_directional_rr(entry, sl, tp, direction)

    if not OPENROUTER_CONFIGURED:
        # Calculate deterministic score
        score, prob, grade = calculate_quality_score(is_valid, rr_ratio, "good")

        return {
            "risk_reward_ratio": round(rr_ratio, 2),
            "risk_reward_text": risk_reward_text,
            "probability_estimate": prob,
            "structure_valid": is_valid,
            "structure_quality": "valid" if is_valid else "invalid",
            "quality_score": score,
            "trade_grade": grade,
            "recommendations": [
                "Configure OPENROUTER_API_KEY for advanced AI validation",
                "Ensure risk:reward is at least 1:2"
            ],
            "warnings": [] if is_valid else ["Invalid structure: Check entry/SL/TP alignment"],
            "mode": "fallback"
        }

    try:
        prompt = f"""Analyze this trade setup:
        Symbol: {symbol}
        Direction: {direction}
        Entry: {entry}
        Stop Loss: {sl}
        Take Profit: {tp}
        Risk:Reward: {risk_reward_text}

        Evaluate:
        1. Is the structure valid (SL below entry for BUY, above for SELL)?
        2. Risk management quality (is {risk_reward_text} favorable?)
        3. Probability estimate based on typical price action
        4. Trade quality score 0-100
        5. Any warnings or recommendations

        Return JSON:
        {{
            "structure_valid": true/false,
            "structure_quality": "excellent|good|fair|poor|invalid",
            "probability_estimate": 0.0-1.0,
            "quality_score": 0-100,
            "risk_reward_assessment": "excellent|good|adequate|poor",
            "recommendations": ["..."],
            "warnings": ["..."]
        }}"""

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
                    "messages": [
                        {"role": "system", "content": "You are a professional trade analyst. Evaluate trade setups objectively."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise HTTPException(503, "AI validation service unavailable")

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON with markdown stripping
            try:
                clean_content = content.strip()
                if clean_content.startswith("`"):
                    clean_content = clean_content.split("`")[1]
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0].strip()

                json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {}
            except:
                result = {}

            # Normalize probability
            prob = result.get("probability_estimate", 0.6)
            if prob <= 0:
                prob = 0.6
            if prob > 1:
                prob = 1
            result["probability_estimate"] = prob

            # Calculate deterministic quality score
            structure_quality = result.get("structure_quality", "good")
            score, deterministic_prob, grade = calculate_quality_score(
                result.get("structure_valid", is_valid), 
                rr_ratio, 
                structure_quality
            )

            # Blend AI probability with deterministic probability
            final_prob = (prob + deterministic_prob) / 2

            return {
                "risk_reward_ratio": round(rr_ratio, 2),
                "risk_reward_text": risk_reward_text,
                "probability_estimate": round(final_prob, 2),
                "structure_valid": result.get("structure_valid", is_valid),
                "structure_quality": structure_quality,
                "quality_score": score,
                "trade_grade": grade,
                "risk_reward_assessment": result.get("risk_reward_assessment", "good"),
                "recommendations": result.get("recommendations", []),
                "warnings": result.get("warnings", []),
                "mode": "ai",
                "configured": True
            }

    except Exception as e:
        print(f"[VALIDATOR ERROR] {e}", flush=True)
        # Fallback to deterministic calculation
        score, prob, grade = calculate_quality_score(is_valid, rr_ratio, "good")
        return {
            "risk_reward_ratio": round(rr_ratio, 2),
            "risk_reward_text": risk_reward_text,
            "probability_estimate": prob,
            "structure_valid": is_valid,
            "structure_quality": "valid" if is_valid else "invalid",
            "quality_score": score,
            "trade_grade": grade,
            "recommendations": ["AI service temporarily unavailable - using fallback calculation"],
            "warnings": [] if is_valid else ["Invalid structure: Check entry/SL/TP alignment"],
            "mode": "fallback"
        }

# ==========================================
# SIGNAL MANAGEMENT ENDPOINTS (Unchanged)
# ==========================================

@router.post("/signal/save")
async def save_signal(
    request: SignalSaveRequest,
    current_user = Depends(get_current_user)
):
    """
    Save AI-generated trade setup as a signal.
    """
    try:
        # Here you would typically save to database
        # For now, return success with signal ID
        signal_id = f"sig_{os.urandom(4).hex()}"

        return {
            "success": True,
            "signal_id": signal_id,
            "message": "Signal saved successfully",
            "signal": {
                "id": signal_id,
                "symbol": request.symbol,
                "direction": request.direction,
                "entry_price": request.entry_price,
                "stop_loss": request.stop_loss,
                "take_profit": request.take_profit,
                "confidence": request.confidence,
                "created_at": "2024-01-01T00:00:00Z",
                "status": "active"
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to save signal: {str(e)}")

# ==========================================
# CHART ANALYSIS (Unchanged)
# ==========================================

@router.post("/chart/analyze-text")
async def analyze_chart_text(
    request: ChartAnalyzeRequest,
    current_user = Depends(get_current_user)
):
    """
    Text-based chart analysis (for descriptions without image).
    For image analysis, use /ai/chart/analyze (chart_analysis.py).
    """
    if not OPENROUTER_CONFIGURED:
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "trading_bias": "neutral",
            "confidence": 0.5,
            "analysis": "AI analysis requires OPENROUTER_API_KEY configuration",
            "trade_setup": None,
            "mode": "fallback"
        }

    try:
        prompt = f"""Analyze this {request.symbol} chart description for {request.timeframe} timeframe:

        Description: {request.description}

        Provide:
        1. Trading bias (bullish/bearish/neutral)
        2. Confidence level (0-1)
        3. Key support/resistance levels
        4. Suggested trade setup if any

        Return as JSON."""

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
                    "messages": [
                        {"role": "system", "content": "You are a technical analyst. Provide structured analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1000
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Try to extract JSON
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        analysis = {
                            "trading_bias": "neutral",
                            "confidence": 0.5,
                            "analysis": content[:500]
                        }
                except:
                    analysis = {
                        "trading_bias": "neutral", 
                        "confidence": 0.5,
                        "analysis": content[:500]
                    }

                return {
                    "symbol": request.symbol,
                    "timeframe": request.timeframe,
                    **analysis,
                    "mode": "ai"
                }
            else:
                raise HTTPException(503, "Chart analysis service unavailable")

    except Exception as e:
        print(f"[CHART TEXT ERROR] {e}", flush=True)
        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "trading_bias": "neutral",
            "confidence": 0,
            "error": str(e),
            "mode": "fallback"
        }

# ==========================================
# COMPATIBILITY NOTE
# ==========================================
# The following endpoints have been MOVED to dedicated routers:
# - /performance/*  -> performance.py (upload-journal, analyze-journal, dashboard, etc.)
# - /chart/analyze (image) -> chart_analysis.py
# 
# This avoids route collisions and maintains clean separation of concerns.
