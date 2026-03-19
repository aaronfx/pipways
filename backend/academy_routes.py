"""
Pipways Trading Academy — Standalone Router v1.0
Responsibilities:
  1. GET  /academy.html     → serve academy.html (primary, mirrors dashboard.html)
  2. GET  /academy          → 301 redirect to /academy.html
  3. All  /learning/*       → full LMS API (moved from learning.py / main.py)

Wire into main.py:
    from .academy_routes import router as academy_router
    app.include_router(academy_router, tags=["Academy"])

Remove from main.py:
    - app.include_router(LEARNING_ROUTER_MAIN, prefix="/learning", ...)
    - app.include_router(LEARNING_ROUTER_FALLBACK, prefix="/learning", ...)
    - The `from . import learning` / `from . import academy_routes` imports
    - The `_HAS_ACADEMY` guard and fallback stubs
"""

import os
import json
import re
import traceback
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx

from .security import get_current_user
from .database import database

router = APIRouter()

# ── Safe field accessor for asyncpg Records (databases 0.9.0) ────────────────
def _user_get(user, key, default=None):
    if user is None:
        return default
    try:
        return user[key]
    except (KeyError, TypeError):
        try:
            return user.get(key, default)
        except AttributeError:
            return default

# ── Locate academy.html ───────────────────────────────────────────────────────
# Checks: frontend/static/ → static/ → same dir as this file
_BASE = Path(__file__).parent

def _find_academy_html() -> Optional[Path]:
    candidates = [
        _BASE.parent / "frontend" / "static" / "academy.html",
        _BASE.parent / "static" / "academy.html",
        _BASE / "academy.html",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

# ── AI (OpenRouter) ───────────────────────────────────────────────────────────
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL    = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

async def _ai(system: str, user_msg: str, max_tokens: int = 800) -> str:
    if not OPENROUTER_API_KEY:
        return "Trading Coach is currently unavailable. Please configure OPENROUTER_API_KEY."
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
        print(f"[TRADING COACH] Error: {e}", flush=True)
        return "I'm having trouble connecting right now. Please try again shortly."


# ══════════════════════════════════════════════════════════════════════════════
# AI DIAGRAM ENGINE v2.0 — Production-grade, classified, template-driven
# ══════════════════════════════════════════════════════════════════════════════

_ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── 1. LESSON CLASSIFICATION ENGINE ──────────────────────────────────────────

def classify_lesson(title: str, content: str) -> str:
    """
    Rule-based classifier. Returns one of:
    price_action | risk_management | indicator | pattern | structure | concept
    No AI needed — fast and deterministic.
    """
    t = (title + " " + content[:400]).lower()

    # Risk management signals
    if any(k in t for k in ["position siz", "lot size", "drawdown", "r:r", "risk:reward",
                              "portfolio heat", "expectancy", "profit factor", "risk per trade",
                              "risk management", "1% risk", "2% risk", "max risk",
                              "account surviv", "account risk"]):
        return "risk_management"
    # risk/reward also qualifies IF combined with stop/entry context
    if ("risk" in t and "reward" in t) or ("stop loss" in t and "take profit" in t and "risk" in t):
        return "risk_management"

    # Indicator signals
    if any(k in t for k in ["rsi", "macd", "stochastic", "bollinger", "atr", "adx",
                              "moving average", "ema", "sma", "momentum indicator",
                              "oscillator", "overbought", "oversold", "crossover",
                              "golden cross", "death cross", "fibonacci"]):
        return "indicator"

    # Pattern signals
    if any(k in t for k in ["head and shoulder", "double top", "double bottom",
                              "flag", "pennant", "wedge", "triangle", "cup and handle",
                              "engulfing", "pin bar", "doji", "hammer", "pattern",
                              "candlestick formation", "chart pattern"]):
        return "pattern"

    # Market structure signals
    if any(k in t for k in ["support", "resistance", "order block", "supply zone",
                              "demand zone", "fair value gap", "bos", "choch",
                              "break of structure", "change of character", "liquidity",
                              "swing high", "swing low", "market structure", "smart money",
                              "institutional", "imbalance"]):
        return "structure"

    # Price action signals
    if any(k in t for k in ["trend", "uptrend", "downtrend", "higher high", "lower low",
                              "price action", "entry", "breakout", "pullback", "retracement",
                              "trendline", "channel", "timeframe", "session", "multi-timeframe",
                              "confluence"]):
        return "price_action"

    return "concept"


# ── 2. CONTENT EXTRACTION ENGINE ─────────────────────────────────────────────

def extract_diagram_context(title: str, content: str) -> dict:
    """
    Extracts key teaching elements from lesson content.
    Returns structured context dict used to build targeted prompts.
    """
    ctx: dict = {
        "concept": title,
        "elements": [],
        "values": {},
        "intent": "",
    }

    text = content[:1200] if content else ""

    # Extract price values (e.g. 1.0850, 1.0800)
    prices = re.findall(r'1\.\d{4}', text)
    if len(prices) >= 1:
        ctx["values"]["price_a"] = prices[0]
    if len(prices) >= 2:
        ctx["values"]["price_b"] = prices[1]
    if len(prices) >= 3:
        ctx["values"]["price_c"] = prices[2]

    # Extract pip values
    pips = re.findall(r'(\d+)\s*pip', text, re.IGNORECASE)
    if pips:
        ctx["values"]["pips"] = pips[0]

    # Extract R:R ratios
    rr = re.findall(r'(\d+:\d+|\d+\.\d+\s*R)', text, re.IGNORECASE)
    if rr:
        ctx["values"]["rr"] = rr[0]

    # Extract percentage values
    pct = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
    if pct:
        ctx["values"]["pct"] = pct[0]

    # Detect key elements mentioned
    checks = {
        "Entry":      ["entry", "buy at", "sell at", "open at"],
        "Stop Loss":  ["stop loss", "stop at", "sl:", "sl ="],
        "Take Profit":["take profit", "target", "tp:", "tp ="],
        "Trend":      ["uptrend", "downtrend", "trend"],
        "Support":    ["support", "demand zone"],
        "Resistance": ["resistance", "supply zone"],
        "Order Block":["order block", "ob zone"],
        "Liquidity":  ["liquidity", "stop hunt"],
        "RSI":        ["rsi", "relative strength"],
        "MACD":       ["macd", "histogram"],
        "Pattern":    ["head and shoulders", "double", "flag", "triangle"],
    }
    tl = text.lower()
    for elem, keywords in checks.items():
        if any(k in tl for k in keywords):
            ctx["elements"].append(elem)

    # Build intent summary (first 2 meaningful sentences)
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 20]
    ctx["intent"] = ". ".join(sentences[:2]) if sentences else title

    return ctx


# ── 3. TEMPLATE-DRIVEN PROMPT SYSTEM ─────────────────────────────────────────

def build_diagram_prompt(classification: str, context: dict, attempt: int = 0) -> str:
    """
    Returns a highly structured, classification-specific prompt.
    Each template guides the AI with zero ambiguity.
    attempt=1 adds "simplify diagram" for retry.
    """
    simplify = "\n\nIMPORTANT: Keep the diagram SIMPLE. Fewer elements, larger labels." if attempt > 0 else ""
    vals = context.get("values", {})
    elems = context.get("elements", [])
    title = context.get("concept", "Forex Concept")
    intent = context.get("intent", title)

    pa = vals.get("price_a", "1.0850")
    pb = vals.get("price_b", "1.0820")
    pc = vals.get("price_c", "1.0890")
    pips_val = vals.get("pips", "20")
    rr_val = vals.get("rr", "1:2")
    pct_val = vals.get("pct", "1")

    if classification == "price_action":
        return f"""Create an SVG price action diagram for: "{title}"

CONTEXT: {intent}

DRAW THIS EXACTLY:
1. A price polyline showing an uptrend (rising from bottom-left to top-right)
2. A horizontal dashed green line labeled "Entry {pa}" 
3. A horizontal dashed red line below entry labeled "Stop Loss {pb}"
4. A horizontal dashed green line above entry labeled "Take Profit {pc}"
5. A filled yellow circle at the entry point on the price line
6. A green upward arrow showing the expected move to TP
7. Annotate the risk zone (red bracket) and reward zone (green bracket) on the right
8. Title: "{title}" in purple at the top
9. Footer text: "R:R = {rr_val} | Risk = {pips_val} pips"

Use polyline for price, dashed lines for levels, circle for entry.{simplify}"""

    if classification == "risk_management":
        return f"""Create an SVG risk management diagram for: "{title}"

CONTEXT: {intent}

DRAW THIS EXACTLY:
1. Title: "{title}" in purple at top
2. Three horizontal bar comparisons side by side:
   - Bar 1 (green, narrow): "1% risk — Safe" — account survives drawdown
   - Bar 2 (yellow, medium): "2% risk — Moderate" — some drawdown  
   - Bar 3 (red, wide): "5%+ risk — Danger" — severe drawdown
3. Show dollar amounts or percentages on each bar
4. Add labels: "Risk Per Trade" on x-axis
5. Add a "DANGER ZONE" red label above the 5% bar
6. Footer: "Professional traders risk 0.5–2% per trade maximum"
7. Show a formula box: "Lot Size = (Account × Risk%) ÷ (SL pips × Pip Value)"{simplify}"""

    if classification == "indicator":
        # Determine which indicator
        tl = title.lower() + " " + intent.lower()
        if "rsi" in tl or "strength" in tl:
            return f"""Create an SVG RSI indicator panel for: "{title}"

DRAW THIS EXACTLY:
1. Title: "{title}" in purple at top
2. A price chart panel (top 40% of SVG) — simple polyline showing price movement
3. Below it, an RSI panel (bottom 50%) with:
   - Horizontal red dashed line at y=70 labeled "70 Overbought"
   - Horizontal green dashed line at y=30 labeled "30 Oversold"  
   - Horizontal grey line at y=50 labeled "50 Midline"
   - RSI line oscillating — dip into oversold zone then bounce up
   - Mark the oversold point with a green circle and "BUY SIGNAL" label
4. Footer: "RSI < 30 = Oversold (look to buy) | RSI > 70 = Overbought (look to sell)"{simplify}"""

        if "macd" in tl:
            return f"""Create an SVG MACD indicator diagram for: "{title}"

DRAW THIS EXACTLY:
1. Title: "{title}" in purple at top
2. Price panel (top 35%) — upward trending polyline
3. MACD panel (bottom 55%) with:
   - Zero line across middle (grey dashed)
   - MACD histogram bars: green bars above zero, red bars below zero
   - MACD signal line (yellow) crossing above histogram = bullish signal
   - Mark the crossover with a yellow circle labeled "Signal"
   - Label: "MACD Line" and "Signal Line"
4. Footer: "MACD crossover above zero = bullish momentum"{simplify}"""

        # Generic indicator (Fibonacci, MA, etc.)
        return f"""Create an SVG indicator/tool diagram for: "{title}"

CONTEXT: {intent}

DRAW THIS EXACTLY:
1. Title: "{title}" in purple at top
2. Price chart (polyline) showing a clear trend
3. Overlay the key levels this indicator produces:
   - For Fibonacci: horizontal lines at 23.6%, 38.2%, 50%, 61.8% with labels
   - For Moving Average: a smooth curved line over price, labeled "MA20" and "MA50"
   - Mark where price bounces off the key level with a green circle
4. Annotate the trading signal clearly
5. Footer: One-line explanation of how to use this indicator{simplify}"""

    if classification == "pattern":
        tl = title.lower()
        if "head" in tl or "shoulder" in tl:
            shape = "head_and_shoulders"
        elif "double" in tl and "bottom" in tl:
            shape = "double_bottom"
        elif "double" in tl and "top" in tl:
            shape = "double_top"
        elif "flag" in tl or "pennant" in tl:
            shape = "flag"
        else:
            shape = "generic"

        shapes = {
            "head_and_shoulders": """Draw a Head and Shoulders pattern:
   - Left shoulder: smaller peak at left
   - Head: taller central peak
   - Right shoulder: smaller peak matching left
   - Neckline: horizontal line connecting the two troughs
   - Red downward arrow after right shoulder showing breakdown
   - Label each part: "Left Shoulder", "Head", "Right Shoulder", "Neckline"
   - Label "SELL SIGNAL" with red arrow pointing down after neckline break""",
            "double_bottom": """Draw a Double Bottom (W pattern):
   - Two equal lows connected by a peak in the middle
   - Resistance line at the peak level (dashed)
   - Green upward arrow after second bottom bounces
   - Label: "Bottom 1", "Bottom 2", "Resistance", "BUY SIGNAL"
   - Show price breaking above resistance with green arrow""",
            "double_top": """Draw a Double Top (M pattern):
   - Two equal highs connected by a trough in the middle  
   - Support line at the trough level (dashed)
   - Red downward arrow after second top rejects
   - Label: "Top 1", "Top 2", "Support/Neckline", "SELL SIGNAL"
   - Show price breaking below support with red arrow""",
            "flag": """Draw a Bull Flag pattern:
   - Strong vertical pole (sharp price surge upward)
   - Consolidation channel sloping slightly downward (the flag)
   - Breakout above channel with green arrow
   - Label: "Pole", "Flag Channel", "Breakout"
   - Show measured move target (same height as pole)""",
            "generic": f"""Draw the chart pattern described by: "{title}"
   - Show the recognizable shape of the pattern
   - Label key points (peaks, troughs, necklines)
   - Show the expected direction after pattern completes
   - Mark entry point with yellow circle
   - Mark target with green dashed line""",
        }

        return f"""Create an SVG chart pattern diagram for: "{title}"

DRAW THIS EXACTLY:
1. Title: "{title}" in purple at top
2. {shapes[shape]}
3. Entry circle (yellow) at the signal point
4. Footer: "Wait for CONFIRMATION before entering — never trade a pattern in progress"{simplify}"""

    if classification == "structure":
        tl = title.lower()
        if "order block" in tl:
            detail = """Draw Order Block diagram:
   - Price impulse: sharp move UP from a red bearish candle (the OB)
   - Mark the last bearish candle before impulse with a green box labeled "Order Block"
   - Dashed return path showing price retracing back to OB
   - Yellow circle at OB zone labeled "Entry Zone"
   - Green arrow from OB pointing up labeled "Expected Move"
   - Label: "Displacement" on the impulse, "Mitigation" on the return"""
        elif "liquidity" in tl:
            detail = """Draw Liquidity Sweep diagram:
   - Price approaching a cluster of equal lows (sell-side liquidity)
   - Price dips BELOW the lows briefly (the sweep) — red wick
   - Immediate rejection and recovery above the lows
   - Mark the sweep zone with red shading labeled "Liquidity Swept"
   - Green circle at recovery point labeled "Entry After Sweep"
   - Show stops being triggered below with small "X" marks
   - Green arrow showing the continuation move after sweep"""
        elif "bos" in tl or "choch" in tl or "structure" in tl:
            detail = """Draw Market Structure diagram:
   - Uptrend with labeled Higher Highs (HH) and Higher Lows (HL)
   - Mark each HH with green circle labeled "HH"
   - Mark each HL with yellow circle labeled "HL"  
   - Show a Break of Structure (BOS): price exceeds previous HH
   - Mark BOS point with purple line and "BOS" label
   - Show potential entry at next HL after BOS"""
        else:
            detail = """Draw Support and Resistance diagram:
   - Price oscillating between two horizontal levels
   - Red dashed line at top labeled "Resistance — sellers dominate"
   - Green dashed line at bottom labeled "Support — buyers dominate"
   - Show price bouncing off support (green arrows up)
   - Show price rejecting resistance (red arrows down)
   - Mark entry at support bounce with yellow circle"""

        return f"""Create an SVG market structure diagram for: "{title}"

CONTEXT: {intent}

DRAW THIS EXACTLY:
1. Title: "{title}" in purple at top
2. {detail}
3. Footer: One sentence explaining when to trade this structure{simplify}"""

    # Default: concept diagram
    return f"""Create an SVG educational diagram for the forex concept: "{title}"

CONTEXT: {intent}

DRAW THIS EXACTLY:
1. Title: "{title}" in purple at top  
2. A clear, minimal visual that illustrates the CORE concept:
   - Use boxes, arrows, and labels to show relationships
   - If it's a calculation: show the formula in a highlighted box with an example
   - If it's a comparison: use side-by-side labeled sections
   - If it's a process: use a simple flowchart with numbered steps
   - If it's a market concept: show a simple annotated price example
3. Use green for positive/bullish outcomes, red for negative/bearish
4. Keep it simple — 5 to 8 elements maximum
5. Footer: One-sentence key takeaway{simplify}"""


# ── 4. MASTER SYSTEM PROMPT ───────────────────────────────────────────────────

_SVG_SYSTEM_PROMPT = """You are a professional SVG diagram generator for a forex trading education platform used by thousands of students.

OUTPUT RULES — MUST FOLLOW EXACTLY:
- Output ONLY raw SVG. Zero markdown. Zero explanation. Zero code fences.
- First character of output must be: <
- Last characters must be: </svg>
- If you cannot comply, output: <svg class="ac-svg-diagram" viewBox="0 0 480 220" xmlns="http://www.w3.org/2000/svg"><rect width="480" height="220" fill="#0d1117" rx="8"/><text x="240" y="110" text-anchor="middle" fill="#a78bfa" font-size="14">Diagram unavailable</text></svg>

SVG SPECIFICATIONS:
- Opening tag: <svg class="ac-svg-diagram" viewBox="0 0 480 220" xmlns="http://www.w3.org/2000/svg">
- Root background rect: <rect width="480" height="220" fill="#0d1117" rx="8"/>
- viewBox: always "0 0 480 220"
- No external references. No images. No scripts. Inline only.
- All text: font-family="Inter, sans-serif"

COLOR SYSTEM (use ONLY these):
- #a78bfa — Title text, labels, purple accents
- #34d399 — Bullish, profit, green zones, upward arrows
- #f87171 — Bearish, loss, red zones, downward arrows
- #fbbf24 — Entry points, highlights, key annotations
- #60a5fa — Secondary labels, neutral info, blue accents
- #9ca3af — Body text, descriptions
- #6b7280 — Footer text, muted labels
- #1f2937 — Dark panel backgrounds
- #e5e7eb — White text on dark backgrounds
- #f59e0b — Orange accents, warnings

LAYOUT RULES:
- Title: centered text at x="240" y="16", fill="#a78bfa", font-size="11", font-weight="bold"
- Footer: centered text at x="240" y="210", fill="#6b7280", font-size="9"
- Main content: between y=25 and y=200
- Leave 20px padding on left and right (x=20 to x=460)
- Price lines: use <polyline> not <path> unless curves are needed
- Key levels: horizontal <line> with stroke-dasharray="4" 
- Entry points: <circle r="5"> filled yellow
- Arrows: use <polygon> or simple lines with markers
- Labels next to elements, never overlapping

QUALITY STANDARDS:
- Every diagram must be immediately understandable by a beginner
- Show actual price numbers or percentages where relevant
- Use arrows to show direction of price movement
- Annotate every key element
- Minimum 6 elements, maximum 20 elements"""


# ── 5. SVG VALIDATION LAYER ───────────────────────────────────────────────────

def validate_svg(svg: str) -> bool:
    """
    Validates AI-generated SVG before saving to DB.
    Returns False if invalid — triggers retry or fallback.
    """
    if not svg or not isinstance(svg, str):
        return False
    svg = svg.strip()
    if not svg.startswith("<svg"):
        return False
    if not svg.rstrip().endswith("</svg>"):
        return False
    if len(svg) < 200:       # Too short — likely a stub
        return False
    if len(svg) > 30000:     # Too long — runaway generation
        return False
    if "<script" in svg.lower():    # Security: no scripts
        return False
    if "javascript:" in svg.lower():
        return False
    if 'class="ac-svg-diagram"' not in svg:
        return False
    # Must have at least a title text element
    if svg.count("<text") < 1:
        return False
    return True


def _fallback_svg(title: str, classification: str) -> str:
    """Returns a clean minimal SVG when generation fails completely."""
    icons = {
        "price_action":    "📈",
        "risk_management": "🛡️",
        "indicator":       "📊",
        "pattern":         "🔷",
        "structure":       "🏗️",
        "concept":         "💡",
    }
    icon = icons.get(classification, "📊")
    safe_title = title.replace('"', "'")[:50]
    return f'''<svg class="ac-svg-diagram" viewBox="0 0 480 220" xmlns="http://www.w3.org/2000/svg">
  <rect width="480" height="220" fill="#0d1117" rx="8"/>
  <rect x="20" y="30" width="440" height="160" fill="#111827" stroke="#1f2937" rx="6"/>
  <text x="240" y="16" text-anchor="middle" fill="#a78bfa" font-size="11" font-weight="bold">{safe_title}</text>
  <text x="240" y="110" text-anchor="middle" fill="#374151" font-size="48">{icon}</text>
  <text x="240" y="155" text-anchor="middle" fill="#4b5563" font-size="12">Visual diagram for this lesson</text>
  <text x="240" y="175" text-anchor="middle" fill="#374151" font-size="10">Open the lesson to study the concepts</text>
  <text x="240" y="210" text-anchor="middle" fill="#6b7280" font-size="9">Trading Academy — Pipways</text>
</svg>'''


# ── 6. MAIN GENERATION FUNCTION WITH RETRY ────────────────────────────────────

async def _generate_diagram(lesson_title: str, lesson_content: str, level_name: str) -> str:
    """
    Production diagram generation pipeline:
    1. Classify lesson type
    2. Extract structured context  
    3. Build targeted prompt from template
    4. Call Anthropic API
    5. Validate SVG output
    6. Retry up to 2 times on failure
    7. Return fallback SVG if all attempts fail
    """
    if not _ANTHROPIC_KEY:
        print("[AI DIAGRAM] ANTHROPIC_API_KEY not set — returning fallback.", flush=True)
        classification = classify_lesson(lesson_title, lesson_content)
        return _fallback_svg(lesson_title, classification)

    # Step 1 & 2: Classify and extract context
    classification = classify_lesson(lesson_title, lesson_content)
    context = extract_diagram_context(lesson_title, lesson_content)
    context["concept"] = lesson_title

    print(f"[AI DIAGRAM] Lesson: '{lesson_title}' | Class: {classification} | Level: {level_name}", flush=True)

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Step 3: Build template-driven prompt
            prompt = build_diagram_prompt(classification, context, attempt)

            # Step 4: Call API
            async with httpx.AsyncClient(timeout=45) as client:
                res = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": _ANTHROPIC_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 2500,
                        "system": _SVG_SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                )

            if res.status_code != 200:
                print(f"[AI DIAGRAM] API error {res.status_code} (attempt {attempt+1})", flush=True)
                continue

            # Extract text from response
            data = res.json()
            svg_text = "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            ).strip()

            # Clean up any code fences
            svg_text = re.sub(r"^```[a-z]*\n?", "", svg_text, flags=re.IGNORECASE)
            svg_text = re.sub(r"\n?```$", "", svg_text).strip()

            # Extract SVG if embedded in text
            if not svg_text.startswith("<svg"):
                match = re.search(r"<svg[\s\S]*?</svg>", svg_text, re.DOTALL)
                if match:
                    svg_text = match.group(0).strip()

            # Ensure required class
            if svg_text.startswith("<svg") and 'class="ac-svg-diagram"' not in svg_text:
                svg_text = svg_text.replace("<svg ", '<svg class="ac-svg-diagram" ', 1)

            # Step 5: Validate
            if validate_svg(svg_text):
                print(f"[AI DIAGRAM] ✅ Generated (attempt {attempt+1}): {lesson_title}", flush=True)
                return svg_text
            else:
                print(f"[AI DIAGRAM] Invalid SVG on attempt {attempt+1} for: {lesson_title}", flush=True)

        except Exception as e:
            print(f"[AI DIAGRAM] Attempt {attempt+1} error: {e}", flush=True)

    # Step 7: All attempts failed — return clean fallback
    print(f"[AI DIAGRAM] All {max_attempts} attempts failed — using fallback for: {lesson_title}", flush=True)
    return _fallback_svg(lesson_title, classification)


def _has_diagram(content: str) -> bool:
    """Check if lesson content already has an SVG diagram."""
    return bool(content and ("<svg" in content or "ac-svg-diagram" in content))



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
# BADGE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

BADGE_DEFINITIONS = {
    "beginner_trader":   {"name": "Beginner Trader",   "icon": "fa-seedling",     "color": "#34d399", "desc": "Completed Beginner level"},
    "technical_analyst": {"name": "Technical Analyst", "icon": "fa-chart-line",   "color": "#60a5fa", "desc": "Completed Intermediate level"},
    "strategy_builder":  {"name": "Strategy Builder",  "icon": "fa-chess-knight", "color": "#a78bfa", "desc": "Completed Advanced level"},
    "pipways_certified": {"name": "Pipways Certified", "icon": "fa-certificate",  "color": "#f59e0b", "desc": "Completed entire Academy curriculum"},
    "quiz_master":       {"name": "Quiz Master",       "icon": "fa-cogs",         "color": "#f472b6", "desc": "Passed 10 quizzes with 80%+"},
    "perfect_score":     {"name": "Perfect Score",     "icon": "fa-medal",        "color": "#fbbf24", "desc": "Scored 100% on any quiz"},
    "risk_manager":      {"name": "Risk Manager",      "icon": "fa-shield-alt",   "color": "#22d3ee", "desc": "Mastered Risk Management modules"},
    "psychology_pro":    {"name": "Psychology Pro",    "icon": "fa-cogs",         "color": "#e879f9", "desc": "Completed Trading Psychology module"},
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
               GROUP BY level_id""", {}
        )
        level_map = {r["level_id"]: r["cnt"]   for r in level_counts} if level_counts else {}
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
            done_all  = sum(level_map.values())
            if done_all >= total_all:
                if await _award_badge(user_id, "pipways_certified"):
                    newly_awarded.append("pipways_certified")

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
                print(f"[BADGE CHECK ERROR] Topic badge check: {e}", flush=True)
    except Exception as e:
        print(f"[BADGE CHECK ERROR] General: {e}", flush=True)
    return newly_awarded

# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/academy.html")
async def serve_academy(request: Request):
    """
    Serve academy.html at /academy.html — mirrors how dashboard.html is served.
    Auth is enforced client-side (JS checks localStorage token and redirects
    to / on 401 from any API call), consistent with how dashboard.html works.
    """
    p = _find_academy_html()
    if p:
        return FileResponse(str(p), media_type="text/html")
    # Graceful fallback — tells the developer where to put the file
    raise HTTPException(
        status_code=404,
        detail=(
            "academy.html not found. "
            "Place it in frontend/static/academy.html or static/academy.html."
        )
    )

@router.get("/academy")
async def academy_clean_url_redirect():
    """Redirect /academy → /academy.html to match the canonical URL pattern."""
    return RedirectResponse(url="/academy.html", status_code=301)

# ══════════════════════════════════════════════════════════════════════════════
# LMS API — /learning/*
# (These were previously mounted via main.py; they now live here exclusively)
# ══════════════════════════════════════════════════════════════════════════════

# ── READ ──────────────────────────────────────────────────────────────────────

@router.get("/learning/levels")
async def get_levels(current_user=Depends(get_current_user)):
    try:
        rows = await database.fetch_all(
            "SELECT id, name, description, order_index FROM learning_levels ORDER BY order_index"
        )
        return [dict(r) for r in (rows or [])]
    except Exception as e:
        print(f"[API ERROR] get_levels: {e}", flush=True)
        return []

@router.get("/learning/modules/{level_id}")
async def get_modules(level_id: int, current_user=Depends(get_current_user)):
    try:
        level = await database.fetch_one(
            "SELECT id FROM learning_levels WHERE id=:lid", {"lid": level_id}
        )
        if not level:
            return []

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
                    "SELECT COUNT(*) FROM learning_lessons WHERE module_id=:mid", {"mid": m["id"]}
                ) or 0
                done = await database.fetch_val(
                    """SELECT COUNT(*) FROM user_learning_progress
                       WHERE user_id=:uid AND module_id=:mid AND completed=TRUE""",
                    {"uid": user_id, "mid": m["id"]}
                ) or 0
                result.append({
                    **dict(m),
                    "lesson_count":    int(total),
                    "completed_count": int(done),
                    "is_complete":     total > 0 and done >= total,
                })
            except Exception as e:
                print(f"[API ERROR] get_modules loop: {e}", flush=True)
                result.append({**dict(m), "lesson_count": 0, "completed_count": 0, "is_complete": False})
        return result
    except Exception as e:
        print(f"[API ERROR] get_modules: {e}", flush=True)
        return []

@router.get("/learning/lessons/{module_id}")
async def get_lessons(module_id: int, current_user=Depends(get_current_user)):
    try:
        module = await database.fetch_one(
            "SELECT id FROM learning_modules WHERE id=:mid", {"mid": module_id}
        )
        if not module:
            return []

        lessons = await database.fetch_all(
            "SELECT id, title, order_index FROM learning_lessons WHERE module_id=:mid ORDER BY order_index",
            {"mid": module_id}
        )
        if not lessons:
            return []

        user_id = current_user.get("id") if current_user else 0
        result = []
        for i, les in enumerate(lessons):
            try:
                progress = await database.fetch_one(
                    """SELECT completed, quiz_score FROM user_learning_progress
                       WHERE user_id=:uid AND lesson_id=:lid""",
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
            except Exception as e:
                print(f"[API ERROR] get_lessons loop: {e}", flush=True)
                result.append({**dict(les), "completed": False, "quiz_score": None, "unlocked": i == 0})
        return result
    except Exception as e:
        print(f"[API ERROR] get_lessons: {e}", flush=True)
        return []

@router.get("/learning/lesson/{lesson_id}")
async def get_lesson(lesson_id: int, current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            """SELECT l.id, l.title, l.content, l.order_index, l.module_id,
                      m.title AS module_title, m.level_id, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m  ON m.id  = l.module_id
               JOIN learning_levels  lv ON lv.id = m.level_id
               WHERE l.id = :lid""",
            {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")

        user_id = current_user.get("id") if current_user else 0
        adj = await database.fetch_all(
            """SELECT l.id, l.title, l.order_index,
                      EXISTS(
                          SELECT 1 FROM user_learning_progress p
                          WHERE p.lesson_id=l.id AND p.user_id=:uid AND p.completed=TRUE
                      ) as completed
               FROM learning_lessons l
               WHERE l.module_id = (SELECT module_id FROM learning_lessons WHERE id=:lid)
               ORDER BY l.order_index""",
            {"lid": lesson_id, "uid": user_id}
        )

        current_idx  = next((i for i, a in enumerate(adj) if a["id"] == lesson_id), -1)
        prev_lesson  = adj[current_idx - 1] if current_idx > 0          else None
        next_lesson  = adj[current_idx + 1] if current_idx < len(adj)-1 else None

        result = dict(lesson)
        result["prev_lesson"] = {"id": prev_lesson["id"], "title": prev_lesson["title"], "completed": prev_lesson["completed"]} if prev_lesson else None
        result["next_lesson"] = {"id": next_lesson["id"], "title": next_lesson["title"], "completed": next_lesson["completed"]} if next_lesson else None
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_lesson: {e}", flush=True)
        raise HTTPException(500, "Failed to load lesson data")

@router.get("/learning/quiz/{lesson_id}")
async def get_quiz(lesson_id: int, current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            "SELECT id FROM learning_lessons WHERE id=:lid", {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")

        questions = await database.fetch_all(
            """SELECT id, question, option_a, option_b, option_c, option_d,
                      correct_answer, explanation, topic_slug
               FROM lesson_quizzes WHERE lesson_id=:lid ORDER BY id""",
            {"lid": lesson_id}
        )
        return {
            "lesson_id":      lesson_id,
            "question_count": len(questions) if questions else 0,
            "questions":      [dict(q) for q in (questions or [])],
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_quiz: {e}", flush=True)
        return {"lesson_id": lesson_id, "question_count": 0, "questions": []}

@router.get("/learning/progress/{user_id}")
async def get_progress(user_id: int, current_user=Depends(get_current_user)):
    try:
        caller   = current_user.get("id")       if current_user else 0
        is_admin = current_user.get("is_admin") if current_user else False
        if caller != user_id and not is_admin:
            return {"user_id": user_id, "total_lessons": 0, "completed_lessons": 0,
                    "completion_rate": 0.0, "progress": [], "summary": []}

        rows   = await database.fetch_all(
            """SELECT p.id, p.level_id, p.module_id, p.lesson_id, p.completed,
                      p.quiz_score, p.completed_at,
                      l.title AS lesson_title, m.title AS module_title
               FROM user_learning_progress p
               LEFT JOIN learning_lessons l ON l.id = p.lesson_id
               LEFT JOIN learning_modules m ON m.id = p.module_id
               WHERE p.user_id = :uid""",
            {"uid": user_id}
        )
        levels = await database.fetch_all(
            "SELECT id, name FROM learning_levels ORDER BY order_index"
        ) or []

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
                    "level_id":   lv["id"],
                    "level_name": lv["name"],
                    "total":      int(total),
                    "completed":  int(done),
                    "percent":    round((int(done) / int(total) * 100) if total else 0, 1),
                })
            except Exception as e:
                print(f"[API ERROR] get_progress summary loop: {e}", flush=True)
                summary.append({"level_id": lv["id"], "level_name": lv["name"],
                                 "total": 0, "completed": 0, "percent": 0.0})

        total_lessons     = await database.fetch_val("SELECT COUNT(*) FROM learning_lessons") or 0
        completed_lessons = sum(1 for p in (rows or []) if p and p.get("completed"))

        return {
            "user_id":          user_id,
            "total_lessons":    int(total_lessons),
            "completed_lessons":completed_lessons,
            "completion_rate":  round((completed_lessons / int(total_lessons) * 100) if total_lessons else 0, 1),
            "progress":         [dict(r) for r in (rows or [])],
            "summary":          summary,
        }
    except Exception as e:
        print(f"[API ERROR] get_progress: {e}", flush=True)
        return {"user_id": user_id, "total_lessons": 0, "completed_lessons": 0,
                "completion_rate": 0.0, "progress": [], "summary": [], "error": "Failed to load progress"}

@router.get("/learning/badges/{user_id}")
async def get_badges(user_id: int, current_user=Depends(get_current_user)):
    try:
        caller   = current_user.get("id")       if current_user else 0
        is_admin = current_user.get("is_admin") if current_user else False
        if caller != user_id and not is_admin:
            return {"user_id": user_id, "badges": [], "count": 0}

        rows = await database.fetch_all(
            "SELECT badge_type, earned_at FROM user_badges WHERE user_id=:uid ORDER BY earned_at DESC",
            {"uid": user_id}
        )
        badges = []
        for r in (rows or []):
            defn = BADGE_DEFINITIONS.get(r["badge_type"], {})
            badges.append({
                "type":      r["badge_type"],
                "badge_type":r["badge_type"],
                "name":      defn.get("name",  r["badge_type"]),
                "icon":      defn.get("icon",  "fa-medal"),
                "color":     defn.get("color", "#a78bfa"),
                "earned_at": r["earned_at"],
            })
        return {"user_id": user_id, "badges": badges, "count": len(badges)}
    except Exception as e:
        print(f"[API ERROR] get_badges: {e}", flush=True)
        return {"user_id": user_id, "badges": [], "count": 0}

@router.get("/learning/mentor/guide/{user_id}")
async def mentor_guide(user_id: int, current_user=Depends(get_current_user)):
    try:
        caller   = current_user.get("id")       if current_user else 0
        is_admin = current_user.get("is_admin") if current_user else False
        if caller != user_id and not is_admin:
            raise HTTPException(403, "Forbidden")

        profile = await database.fetch_one(
            "SELECT first_academy_visit, weak_topics FROM user_learning_profile WHERE user_id=:uid",
            {"uid": user_id}
        )
        first_visit = (not profile) or bool(profile.get("first_academy_visit", True))

        next_lesson = await database.fetch_one(
            """SELECT l.id, l.title FROM learning_lessons l
               LEFT JOIN user_learning_progress p
                   ON p.lesson_id=l.id AND p.user_id=:uid AND p.completed=TRUE
               WHERE p.id IS NULL
               ORDER BY l.id LIMIT 1""",
            {"uid": user_id}
        )

        if first_visit:
            msg = ("Welcome to the Pipways Trading Academy! 🎓 You're about to start a structured journey "
                   "from Forex fundamentals to professional strategy. Each lesson builds on the last — "
                   "take them in order and complete every quiz before moving on.")
        else:
            weak_raw = profile.get("weak_topics", "[]") if profile else "[]"
            try:
                weak = json.loads(weak_raw) if isinstance(weak_raw, str) else (weak_raw or [])
            except Exception:
                weak = []
            if weak:
                areas = ", ".join(weak[:2])
                msg = (f"Welcome back! Based on your recent quizzes, focus extra attention on {areas}. "
                       "Review those concepts before tackling the next lesson.")
            else:
                msg = "Welcome back! Great progress — keep going and you'll complete the curriculum soon."

        return {
            "first_visit": first_visit,
            "message":     msg,
            "next_lesson": {"id": next_lesson["id"], "title": next_lesson["title"]} if next_lesson else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] mentor_guide: {e}", flush=True)
        return {"first_visit": True, "message": "Welcome to the Trading Academy!", "next_lesson": None}

# ── WRITE ─────────────────────────────────────────────────────────────────────

@router.post("/learning/badges/check")
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

@router.post("/learning/quiz/submit")
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

        q_map   = {q["id"]: q for q in questions}
        total   = len(questions)
        correct = 0
        results = []
        wrong_slugs   = []
        correct_slugs = []

        for ans in payload.answers:
            try:
                selected  = ans.selected_answer.upper()
                row       = q_map.get(ans.question_id)
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
                       VALUES (:uid, :lid, :qid, :ans, :ok, NOW())
                       ON CONFLICT (user_id, question_id) DO UPDATE SET
                       selected_answer=EXCLUDED.selected_answer,
                       is_correct=EXCLUDED.is_correct,
                       answered_at=NOW()""",
                    {"uid": user_id, "lid": payload.lesson_id,
                     "qid": ans.question_id, "ans": selected, "ok": is_correct}
                )
                results.append({
                    "question_id":    ans.question_id,
                    "is_correct":     is_correct,
                    "correct_answer": row["correct_answer"],
                    "explanation":    row["explanation"],
                })
            except Exception as e:
                print(f"[API ERROR] submit_quiz answer loop: {e}", flush=True)

        score  = round((correct / total * 100) if total else 0, 1)
        passed = score >= 70

        if passed:
            await _mark_lesson_complete(user_id, payload.lesson_id, score)
        await _update_learning_profile(user_id, wrong_slugs, correct_slugs)
        new_badges = await _check_and_award_badges(user_id, payload.lesson_id, score)

        lesson = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m  ON m.id=l.module_id
               JOIN learning_levels  lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": payload.lesson_id}
        )
        feedback = _quiz_feedback(
            score, passed,
            lesson["title"]      if lesson else "this lesson",
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] submit_quiz: {e}", flush=True)
        raise HTTPException(500, "Failed to submit quiz")

@router.post("/learning/lesson/complete")
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

@router.post("/learning/profile/first-visit-complete")
async def mark_first_visit_complete(current_user=Depends(get_current_user)):
    try:
        user_id = current_user.get("id") if current_user else 0
        if not user_id:
            raise HTTPException(401, "Not authenticated")

        existing = await database.fetch_one(
            "SELECT id FROM user_learning_profile WHERE user_id=:uid", {"uid": user_id}
        )
        if existing:
            await database.execute(
                "UPDATE user_learning_profile SET first_academy_visit=FALSE WHERE user_id=:uid",
                {"uid": user_id}
            )
        else:
            await database.execute(
                """INSERT INTO user_learning_profile (user_id, first_academy_visit, last_updated)
                   VALUES (:uid, FALSE, NOW())""",
                {"uid": user_id}
            )
        return {"success": True}
    except Exception as e:
        print(f"[API ERROR] mark_first_visit_complete: {e}", flush=True)
        raise HTTPException(500, "Failed to update profile")

# ── AI MENTOR endpoints ───────────────────────────────────────────────────────

@router.post("/learning/mentor/teach")
async def mentor_teach(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            """SELECT l.title, l.content, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m  ON m.id=l.module_id
               JOIN learning_levels  lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")

        system = (
            "You are an expert Forex trading coach. Explain trading concepts clearly "
            "with real examples. Use practical analogies. Be concise (under 200 words). "
            "Format: brief overview, key insight, practical tip."
        )
        content_preview = (lesson.get("content") or "")[:500]
        explanation = await _ai(
            system,
            f"Teach the concept: '{lesson['title']}' at {lesson['level_name']} level. "
            f"Context: {content_preview}"
        )
        return {"lesson_title": lesson["title"], "explanation": explanation}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] mentor_teach: {e}", flush=True)
        return {"lesson_title": "Lesson", "explanation": "Trading Coach is temporarily unavailable. Please review the lesson material and try again."}

@router.post("/learning/mentor/practice")
async def mentor_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m  ON m.id=l.module_id
               JOIN learning_levels  lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")

        system = (
            "Create a short practical trading scenario exercise. Include: scenario description, "
            "a decision point question, and a model answer. Use realistic prices. "
            "Use different currency pairs each time. Under 180 words."
        )
        exercise = await _ai(
            system,
            f"Create exercise for '{lesson['title']}' at {lesson['level_name']} level."
        )
        return {"lesson_title": lesson["title"], "exercise": exercise}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] mentor_practice: {e}", flush=True)
        return {
            "lesson_title": "Practice",
            "exercise": (
                "Practice Exercise:\n\nScenario: EUR/USD is testing a key support level at 1.0850 "
                "after a downtrend.\n\nQuestion: What factors should you check before deciding to buy "
                "at support?\n\nModel Answer: Check 1) Higher timeframe trend direction, 2) Bullish "
                "candlestick patterns (pin bar, engulfing), 3) RSI for oversold conditions, "
                "4) Volume confirmation on the bounce. Only enter if multiple factors align."
            ),
        }

@router.post("/learning/mentor/chart-practice")
async def mentor_chart_practice(lesson_id: int = Query(...), current_user=Depends(get_current_user)):
    try:
        lesson = await database.fetch_one(
            """SELECT l.title, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m  ON m.id=l.module_id
               JOIN learning_levels  lv ON lv.id=m.level_id
               WHERE l.id=:lid""",
            {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")

        system = (
            'Create a chart-reading exercise. Return valid JSON with keys: '
            'tv_symbol (e.g. FX:EURUSD), tv_interval (60), '
            'scenario, question, options [A,B,C,D], correct (A/B/C/D), explanation. '
            'No text outside JSON.'
        )
        level = lesson.get("level_name", "Beginner").lower()
        complexity = {
            "beginner":     "support/resistance identification",
            "intermediate": "trend context with S/R",
            "advanced":     "order blocks, liquidity sweeps, market structure",
        }.get(level, "support and resistance")

        raw = await _ai(system, f"Create chart exercise for '{lesson['title']}' focusing on {complexity}.")

        try:
            clean = raw.strip().strip("```json").strip("```").strip()
            data  = json.loads(clean)
        except Exception:
            data = {
                "tv_symbol":   "FX:EURUSD",
                "tv_interval": "60",
                "scenario":    "EUR/USD H4 shows uptrend with pullback to 1.0850 support.",
                "question":    "Based on trend context, what would you expect at support?",
                "options":     ["A: Buy the bounce", "B: Sell the break", "C: Wait", "D: No trade"],
                "correct":     "A",
                "explanation": "In an uptrend, pullbacks to support offer high-probability long entries.",
            }
        return {
            "lesson_title":  lesson["title"],
            "level":         lesson["level_name"],
            "chart_practice": data,
            # surface keys the JS already expects:
            "question":    data.get("question", ""),
            "options":     data.get("options",  []),
            "correct":     data.get("correct",  "A"),
            "explanation": data.get("explanation", ""),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] mentor_chart_practice: {e}", flush=True)
        fallback = {
            "tv_symbol":   "FX:EURUSD",
            "tv_interval": "60",
            "scenario":    "EUR/USD H4 shows uptrend with pullback to 1.0850 support.",
            "question":    "Based on trend context, what would you expect at support?",
            "options":     ["A: Buy the bounce", "B: Sell the break", "C: Wait", "D: No trade"],
            "correct":     "A",
            "explanation": "In an uptrend, pullbacks to support offer high-probability long entries.",
        }
        return {"lesson_title": "Chart Practice", "level": "Beginner",
                "chart_practice": fallback, **fallback}


# ══════════════════════════════════════════════════════════════════════════════
# AI DIAGRAM ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/learning/lesson/{lesson_id}/diagram")
async def get_lesson_diagram(lesson_id: int, current_user=Depends(get_current_user)):
    """
    Returns an SVG diagram for a lesson.
    - Lesson already has SVG → return it immediately (cached in DB).
    - No SVG yet → generate via Anthropic, save to DB, return it.
    Generation happens ONCE per lesson. All future calls are instant.
    """
    try:
        lesson = await database.fetch_one(
            """SELECT l.id, l.title, l.content, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id = l.module_id
               JOIN learning_levels lv ON lv.id = m.level_id
               WHERE l.id = :lid""",
            {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")

        existing_content = lesson["content"] or ""

        # Already has diagram — extract and return it
        if _has_diagram(existing_content):
            match = re.search(r'<svg[^>]*class="ac-svg-diagram"[^>]*>.*?</svg>', existing_content, re.DOTALL)
            if not match:
                match = re.search(r'<svg[^>]*>.*?</svg>', existing_content, re.DOTALL)
            if match:
                return {"lesson_id": lesson_id, "svg": match.group(0), "cached": True}

        # Generate new diagram via Anthropic
        svg = await _generate_diagram(
            lesson_title=lesson["title"],
            lesson_content=existing_content,
            level_name=lesson["level_name"],
        )

        if not svg:
            return {"lesson_id": lesson_id, "svg": "", "cached": False, "error": "Generation unavailable"}

        # Append SVG to lesson content in DB (permanent cache)
        separator = "\n\n---\n\n## 📊 Chart Diagram\n\n"
        new_content = existing_content.rstrip() + separator + svg
        await database.execute(
            "UPDATE learning_lessons SET content = :c WHERE id = :id",
            {"c": new_content, "id": lesson_id},
        )
        print(f"[AI DIAGRAM] Saved to DB: lesson {lesson_id} — {lesson['title']}", flush=True)

        return {"lesson_id": lesson_id, "svg": svg, "cached": False}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI DIAGRAM ERROR] get_lesson_diagram: {e}", flush=True)
        raise HTTPException(500, f"Diagram generation failed: {e}")


@router.post("/learning/lesson/{lesson_id}/diagram/regenerate")
async def regenerate_lesson_diagram(lesson_id: int, current_user=Depends(get_current_user)):
    """Admin only: force-regenerate the AI diagram for a lesson."""
    is_admin = _user_get(current_user, "is_admin", False)
    if not is_admin:
        raise HTTPException(403, "Admin only")
    try:
        lesson = await database.fetch_one(
            """SELECT l.id, l.title, l.content, lv.name AS level_name
               FROM learning_lessons l
               JOIN learning_modules m ON m.id = l.module_id
               JOIN learning_levels lv ON lv.id = m.level_id
               WHERE l.id = :lid""",
            {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")

        # Strip previous AI diagram section
        clean = re.sub(
            r'\n*---\n+## 📊 (AI-Generated Diagram|Chart Diagram)\n+<svg.*?</svg>',
            '', lesson["content"] or "", flags=re.DOTALL
        ).rstrip()

        svg = await _generate_diagram(lesson["title"], clean, lesson["level_name"])
        if not svg:
            raise HTTPException(503, "Diagram generation unavailable — check ANTHROPIC_API_KEY")

        new_content = clean + "\n\n---\n\n## 📊 Chart Diagram\n\n" + svg
        await database.execute(
            "UPDATE learning_lessons SET content = :c WHERE id = :id",
            {"c": new_content, "id": lesson_id},
        )
        return {"status": "success", "lesson_id": lesson_id, "title": lesson["title"], "svg": svg}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_json(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except Exception:
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
            "SELECT id FROM user_learning_progress WHERE user_id=:uid AND lesson_id=:lid",
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
                {"uid": user_id, "lv": lesson["level_id"],
                 "mid": lesson["module_id"], "lid": lesson_id, "score": score}
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
            cur_weak   = _parse_json(existing.get("weak_topics"))
            cur_strong = _parse_json(existing.get("strong_topics"))
            new_weak   = list(set(cur_weak   + wrong_slugs)   - set(correct_slugs))
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

def _quiz_feedback(score: float, passed: bool, lesson_title: str, wrong_slugs: list, level: str) -> str:
    try:
        if score == 100:
            return f"Perfect mastery! You've demonstrated complete understanding of {lesson_title}. Ready for the next challenge?"
        if passed:
            if wrong_slugs:
                areas = ", ".join(wrong_slugs[:2])
                return f"Strong performance on {lesson_title}! Just polish your understanding of {areas}, then continue forward."
            return f"Great work passing {lesson_title}! Your trading knowledge is building steadily."
        focus  = ", ".join(wrong_slugs[:3]) if wrong_slugs else "the core concepts"
        advice = {
            "beginner":     "Every professional trader started here. Take time to review",
            "intermediate": "Precision separates profitable traders. Revisit",
            "advanced":     "Institutional-grade trading demands mastery. Deep-dive into",
        }.get(level, "Focus your study on")
        return f"{advice} {focus} in {lesson_title}. Reattempt the quiz when the concepts click."
    except Exception:
        return "Continue studying the material and retry the quiz when you feel confident."
