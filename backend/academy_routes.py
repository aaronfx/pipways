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
    Returns a precise, coordinate-driven prompt per lesson classification.
    Exact pixel positions prevent label overlap and layout inconsistency.
    attempt > 0 adds a simplification instruction for retries.
    """
    simplify = "\n\nIMPORTANT: Simplify. Use fewer elements. Make labels larger and further apart." if attempt > 0 else ""
    vals  = context.get("values", {})
    title = context.get("concept", "Forex Concept")
    intent = context.get("intent", title)
    tl    = title.lower() + " " + intent.lower()

    pa      = vals.get("price_a", "1.0850")
    pb      = vals.get("price_b", "1.0820")
    pc      = vals.get("price_c", "1.0890")
    pips_val = vals.get("pips", "20")
    rr_val  = vals.get("rr", "1:2")

    # ── PRICE ACTION ─────────────────────────────────────────────────────────
    if classification == "price_action":
        return f"""Create an SVG price action diagram. Title: "{title}"

EXACT ELEMENTS — place each at the coordinates given:

1. Background: <rect width="480" height="220" fill="#0d1117" rx="8"/>
2. Title: x=240 y=16 text-anchor=middle fill=#a78bfa font-size=11 font-weight=bold

3. Price polyline (uptrend):
   points="30,185 80,165 130,170 180,140 220,148 260,115 300,125 350,95 400,100 450,75"
   stroke=#34d399 stroke-width=2 fill=none

4. Entry level line: x1=30 y1=130 x2=370 y2=130 stroke=#fbbf24 stroke-width=1.5 stroke-dasharray=4
5. Stop Loss line:   x1=30 y1=158 x2=370 y2=158 stroke=#f87171 stroke-width=1.5 stroke-dasharray=4
6. Take Profit line: x1=30 y1=100 x2=370 y2=100 stroke=#34d399 stroke-width=1.5 stroke-dasharray=4

7. Entry circle: cx=220 cy=130 r=6 fill=#fbbf24

8. RIGHT-SIDE LABELS (x=375, stacked 28px apart — NO overlap):
   - "Entry {pa}"         x=375 y=128 fill=#fbbf24 font-size=9
   - "Stop Loss {pb}"     x=375 y=156 fill=#f87171 font-size=9
   - "Take Profit {pc}"   x=375 y=98  fill=#34d399 font-size=9

9. Risk bracket:   vertical line x=460 y1=130 y2=158 stroke=#f87171 stroke-width=1
   Label "Risk"    x=465 y=147 fill=#f87171 font-size=8
10. Reward bracket: vertical line x=460 y1=100 y2=130 stroke=#34d399 stroke-width=1
    Label "Reward"  x=463 y=118 fill=#34d399 font-size=8

11. Green arrow pointing up: at x=300 y=108, triangle pointing up fill=#34d399

12. Footer: x=240 y=215 text-anchor=middle fill=#6b7280 font-size=9
    Text: "R:R = {rr_val}  |  Risk = {pips_val} pips  |  Entry {pa}  |  SL {pb}  |  TP {pc}"{simplify}"""

    # ── RISK MANAGEMENT ──────────────────────────────────────────────────────
    if classification == "risk_management":
        if any(k in tl for k in ["leverage", "margin", "lot"]):
            return f"""Create an SVG leverage comparison diagram. Title: "{title}"

EXACT ELEMENTS:

1. Background + Title (standard)

2. THREE HORIZONTAL BARS — each starts at x=30, labels to the RIGHT:

Bar 1 (y=65, height=22, green #34d399, fill-opacity=0.85):
   rect x=30 y=65 width=80 height=22 fill=#34d399 rx=3
   Label: x=118 y=81 fill=#34d399 font-size=9 "1:1 — $1,000 controls $1,000"

Bar 2 (y=105, height=22, yellow #fbbf24, fill-opacity=0.85):
   rect x=30 y=105 width=170 height=22 fill=#fbbf24 rx=3
   Label: x=208 y=121 fill=#fbbf24 font-size=9 "1:10 — $1,000 controls $10,000"

Bar 3 (y=145, height=22, red #f87171, fill-opacity=0.85):
   rect x=30 y=145 width=330 height=22 fill=#f87171 rx=3
   Label: x=368 y=161 fill=#f87171 font-size=9 "1:100 — $1,000 controls $100,000 ⚠"

3. Section label: x=30 y=55 fill=#9ca3af font-size=9 "Leverage Level → Position Size"

4. Warning box: rect x=30 y=178 width=420 height=18 fill=#1f2937 rx=3
   Text: x=240 y=191 text-anchor=middle fill=#f59e0b font-size=9 "Higher leverage = larger position = bigger risk per pip"

5. Footer: "Higher leverage amplifies both profits AND losses — use with caution"{simplify}"""

        if any(k in tl for k in ["stop loss", "take profit", "risk reward", "r:r"]):
            return f"""Create an SVG risk vs reward diagram. Title: "{title}"

EXACT ELEMENTS:

1. Background + Title (standard)

2. Price line (vertical entry then move):
   polyline points="70,170 70,80 240,50" stroke=#60a5fa stroke-width=2 fill=none

3. Entry horizontal line: x1=30 y1=130 x2=450 y2=130 stroke=#fbbf24 stroke-width=1.5 stroke-dasharray=4
   Entry circle: cx=70 cy=130 r=6 fill=#fbbf24
   Label "Entry {pa}" x=455 y=128 text-anchor=end fill=#fbbf24 font-size=9

4. Stop Loss line: x1=30 y1=168 x2=450 y2=168 stroke=#f87171 stroke-width=1.5 stroke-dasharray=4
   Label "Stop Loss {pb}" x=455 y=166 text-anchor=end fill=#f87171 font-size=9

5. Take Profit line: x1=30 y1=88 x2=450 y2=88 stroke=#34d399 stroke-width=1.5 stroke-dasharray=4
   Label "Take Profit {pc}" x=455 y=86 text-anchor=end fill=#34d399 font-size=9

6. RED ZONE (risk area): rect x=72 y=130 width=120 height=38 fill=#f87171 fill-opacity=0.1 stroke=none
   Label "RISK {pips_val} pips" x=132 y=152 text-anchor=middle fill=#f87171 font-size=9

7. GREEN ZONE (reward area): rect x=72 y=88 width=120 height=42 fill=#34d399 fill-opacity=0.1 stroke=none
   Label "REWARD" x=132 y=110 text-anchor=middle fill=#34d399 font-size=9

8. R:R label (large, prominent): x=300 y=135 fill=#fbbf24 font-size=22 font-weight=bold text-anchor=middle
   Text: "{rr_val}"
   Sub-label: x=300 y=150 fill=#6b7280 font-size=9 text-anchor=middle "Risk : Reward"

9. Footer: "Never risk more than 2% per trade. Aim for minimum 1:2 risk:reward."{simplify}"""

        # Position sizing / general risk management
        return f"""Create an SVG position sizing diagram. Title: "{title}"

EXACT ELEMENTS:

1. Background + Title (standard)

2. Formula box: rect x=30 y=32 width=420 height=30 fill=#1f2937 stroke=#7c3aed stroke-width=1 rx=5
   Text: x=240 y=52 text-anchor=middle fill=#c4b5fd font-size=10 font-weight=bold
   "Lot Size = (Account × Risk%) ÷ (Stop Pips × Pip Value)"

3. Example box: rect x=30 y=72 width=420 height=28 fill=#0d1117 stroke=#1f2937 rx=4
   Text: x=240 y=91 text-anchor=middle fill=#9ca3af font-size=9
   "$10,000 × 1% = $100 ÷ (20 pips × $1) = 0.5 mini lots"

4. THREE RISK BARS (stacked, starting y=112, height=20, gap=8):

Bar 1: rect x=30 y=112 width=80  height=20 fill=#34d399 rx=3
   Label: x=118 y=126 fill=#34d399 font-size=9 "1% risk — Safe ($100 on $10k)"

Bar 2: rect x=30 y=140 width=160 height=20 fill=#fbbf24 rx=3
   Label: x=198 y=154 fill=#fbbf24 font-size=9 "3% risk — Caution ($300 on $10k)"

Bar 3: rect x=30 y=168 width=300 height=20 fill=#f87171 rx=3
   Label: x=338 y=182 fill=#f87171 font-size=9 "10% risk — DANGER ($1,000 on $10k)"

5. Footer: "Professional traders risk 0.5–2% maximum per trade"{simplify}"""

    # ── INDICATORS ───────────────────────────────────────────────────────────
    if classification == "indicator":

        if "rsi" in tl or ("relative strength" in tl and "fibonacci" not in tl):
            return f"""Create an SVG RSI indicator panel. Title: "{title}"

EXACT TWO-PANEL LAYOUT:

PANEL 1 — PRICE (y=28 to y=90):
rect x=20 y=28 width=440 height=62 fill=#111827 rx=4
Label "Price" x=30 y=40 fill=#60a5fa font-size=9
Price polyline: points="30,82 75,70 120,75 165,58 210,65 255,50 300,60 345,45 390,52 435,42"
stroke=#60a5fa stroke-width=2 fill=none

PANEL 2 — RSI (y=96 to y=200):
rect x=20 y=96 width=440 height=104 fill=#111827 rx=4

Level lines (INSIDE panel, x1=25 x2=455):
- Overbought (70): y=114 stroke=#f87171 stroke-width=1 stroke-dasharray=4
  Label "70 Overbought" x=430 y=112 text-anchor=end fill=#f87171 font-size=9

- Midline (50): y=148 stroke=#374151 stroke-width=1 stroke-dasharray=2
  Label "50" x=462 y=151 fill=#6b7280 font-size=9

- Oversold (30): y=182 stroke=#34d399 stroke-width=1 stroke-dasharray=4
  Label "30 Oversold" x=430 y=181 text-anchor=end fill=#34d399 font-size=9

RSI line: points="30,145 75,138 120,143 165,128 210,180 255,168 300,148 345,132 390,126 435,130"
stroke=#a78bfa stroke-width=2 fill=none

Oversold signal circle: cx=210 cy=180 r=5 fill=#34d399
Signal label: x=218 y=178 fill=#34d399 font-size=9 "BUY"

Footer: x=240 y=215 text-anchor=middle fill=#6b7280 font-size=9
"RSI below 30 = oversold (buy signal) | RSI above 70 = overbought (sell signal)"{simplify}"""

        if "macd" in tl:
            return f"""Create an SVG MACD indicator diagram. Title: "{title}"

EXACT TWO-PANEL LAYOUT:

PANEL 1 — PRICE (y=28 to y=80):
rect x=20 y=28 width=440 height=52 fill=#111827 rx=4
Label "Price" x=30 y=40 fill=#60a5fa font-size=9
Price polyline: points="30,72 90,62 150,66 210,50 270,55 330,42 390,46 440,36"
stroke=#60a5fa stroke-width=2 fill=none

PANEL 2 — MACD (y=86 to y=200):
rect x=20 y=86 width=440 height=114 fill=#111827 rx=4

Zero line: x1=25 y1=143 x2=455 y2=143 stroke=#374151 stroke-width=1 stroke-dasharray=3
Label "0" x=462 y=146 fill=#6b7280 font-size=9

HISTOGRAM BARS (width=14 each, spaced 18px, y-axis centered on y=143):
Green bars ABOVE zero (top edge to y=143):
  rect x=32  y=122 width=14 height=21 fill=#34d399 rx=1 opacity=0.8
  rect x=50  y=118 width=14 height=25 fill=#34d399 rx=1 opacity=0.8
  rect x=68  y=126 width=14 height=17 fill=#34d399 rx=1 opacity=0.8
  rect x=86  y=135 width=14 height=8  fill=#34d399 rx=1 opacity=0.8
Red bars BELOW zero (y=143 to bottom):
  rect x=104 y=143 width=14 height=14 fill=#f87171 rx=1 opacity=0.8
  rect x=122 y=143 width=14 height=22 fill=#f87171 rx=1 opacity=0.8
  rect x=140 y=143 width=14 height=16 fill=#f87171 rx=1 opacity=0.8
  rect x=158 y=143 width=14 height=6  fill=#f87171 rx=1 opacity=0.8
Green bars resuming:
  rect x=176 y=130 width=14 height=13 fill=#34d399 rx=1 opacity=0.8
  rect x=194 y=122 width=14 height=21 fill=#34d399 rx=1 opacity=0.8
  rect x=212 y=115 width=14 height=28 fill=#34d399 rx=1 opacity=0.8

MACD line (blue):
  polyline points="32,130 68,128 104,150 140,158 176,138 212,122 280,118 360,114 440,108"
  stroke=#60a5fa stroke-width=2 fill=none
Signal line (yellow):
  polyline points="32,133 68,132 104,146 140,154 176,142 212,128 280,122 360,116 440,110"
  stroke=#fbbf24 stroke-width=1.5 fill=none stroke-dasharray=3

Bullish crossover circle: cx=176 cy=140 r=6 fill=none stroke=#fbbf24 stroke-width=2
Label "Cross" x=185 y=138 fill=#fbbf24 font-size=9

Legend (bottom-right, spaced 16px apart):
  "— MACD" x=320 y=188 fill=#60a5fa font-size=9
  "— Signal" x=370 y=188 fill=#fbbf24font-size=9

Footer: "MACD line crosses above signal = bullish momentum building"{simplify}"""

        if "fibonacci" in tl or "fib" in tl:
            return f"""Create an SVG Fibonacci retracement diagram. Title: "{title}"

EXACT ELEMENTS:

1. Background + Title (standard)

2. Price upswing then pullback:
   Impulse up: polyline points="30,190 200,50" stroke=#34d399 stroke-width=2 fill=none
   Retracement: polyline points="200,50 280,110 320,98" stroke=#60a5fa stroke-width=1.5 fill=none stroke-dasharray=3

3. FIBONACCI LEVELS — horizontal lines with labels on RIGHT (x=400+):
   Each line x1=30, x2=390. Labels at x=395, spaced minimum 16px apart on y-axis:

   0% level:   y=50  stroke=#e5e7eb  label "0% — 1.0900"    x=395 y=48  fill=#9ca3af font-size=9
   23.6% level: y=86  stroke=#60a5fa  label "23.6% — 1.0822" x=395 y=84  fill=#60a5fa font-size=9
   38.2% level: y=107 stroke=#a78bfa  label "38.2% — 1.0771" x=395 y=105 fill=#a78bfa font-size=9
   50% level:  y=120 stroke=#fbbf24  label "50% — 1.0725"   x=395 y=118 fill=#fbbf24 font-size=9
   61.8% level: y=133 stroke=#f59e0b  label "61.8% — 1.0680" x=395 y=131 fill=#f59e0b font-size=9  ← GOLDEN RATIO
   78.6% level: y=151 stroke=#f87171  label "78.6% — 1.0625" x=395 y=149 fill=#f87171 font-size=9
   100% level: y=190 stroke=#e5e7eb  label "100% — 1.0500"  x=395 y=188 fill=#9ca3af font-size=9

4. Entry circle at 61.8%: cx=280 cy=133 r=6 fill=#fbbf24
   Label "Entry Zone" x=250 y=128 fill=#fbbf24 font-size=9

5. "GOLDEN RATIO" label: x=200 y=131 fill=#f59e0b font-size=8 font-style=italic "← Golden Ratio"

Footer: "61.8% retracement is the highest-probability reversal zone — use with confluence"{simplify}"""

        if any(k in tl for k in ["moving average", "ma ", "ema", "sma", "crossover", "golden cross"]):
            return f"""Create an SVG moving average crossover diagram. Title: "{title}"

EXACT ELEMENTS:

1. Background + Title (standard)

2. Price line (faint): points="30,170 90,155 150,158 210,135 270,140 330,115 390,118 450,95"
   stroke=#374151 stroke-width=1.5 fill=none

3. MA20 FAST (green — reacts quicker):
   points="30,175 90,158 150,155 210,130 270,135 330,108 390,110 450,88"
   stroke=#34d399 stroke-width=2 fill=none

4. MA50 SLOW (orange — lags behind):
   points="30,182 90,172 150,168 210,158 270,150 330,135 390,125 450,108"
   stroke=#f59e0b stroke-width=2 fill=none

5. GOLDEN CROSS (where MA20 crosses above MA50):
   Circle: cx=270 cy=143 r=8 fill=none stroke=#fbbf24 stroke-width=2
   Label "Golden Cross": x=282 y=136 fill=#fbbf24 font-size=9 font-weight=bold
   Label "BUY ↑": x=282 y=150 fill=#34d399 font-size=9
   NOTE: "Golden Cross" at y=136 and "BUY ↑" at y=150 — 14px apart, NO overlap

6. LEGEND (bottom-left, y=175 and y=190 — 15px apart):
   Green line + "MA20 (Fast)" x=55 y=178 fill=#34d399 font-size=9
   Orange line + "MA50 (Slow)" x=55 y=193 fill=#f59e0b font-size=9

7. Label "BUY when MA20 crosses ABOVE MA50" x=240 y=55 text-anchor=middle fill=#34d399 font-size=9

Footer: "MA20 crosses above MA50 = Golden Cross (buy signal). Below = Death Cross (sell)."{simplify}"""

        # Generic indicator fallback
        return f"""Create an SVG indicator diagram. Title: "{title}"

CONTEXT: {intent}

DRAW THIS EXACTLY:
1. Title "{title}" at standard position
2. A price panel (top 40%, y=28–105): rect fill=#111827, price polyline trending upward
3. An indicator panel (bottom 50%, y=110–200): rect fill=#111827
4. In the indicator panel show the key signal levels as horizontal dashed lines
5. Show the indicator line oscillating, marking the key signal point with a yellow circle
6. Label each level clearly on the RIGHT side (x=430+), one per line, 14px apart
7. Add a legend at bottom showing what each line color means
Footer: Explain in one sentence when to act on this indicator{simplify}"""

    # ── PATTERNS ─────────────────────────────────────────────────────────────
    if classification == "pattern":

        if any(k in tl for k in ["candlestick", "candle", "doji", "hammer", "engulf", "pin bar", "inside bar"]):
            return f"""Create an SVG candlestick anatomy diagram. Title: "{title}"

EXACT COORDINATES — TWO CANDLES WELL SEPARATED, LABELS IN CENTER:

LEFT CANDLE — Bullish (centered at x=115):
  Upper wick: x1=115 y1=42 x2=115 y2=62 stroke=#34d399 stroke-width=2
  Body rect:  x=90 y=62 width=50 height=94 fill=#0d2818 stroke=#34d399 stroke-width=2 rx=2
  Lower wick: x1=115 y1=156 x2=115 y2=176 stroke=#34d399 stroke-width=2
  Top label:  x=115 y=34 text-anchor=middle fill=#34d399 font-size=10 font-weight=bold "Bullish (Green)"

RIGHT CANDLE — Bearish (centered at x=335):
  Upper wick: x1=335 y1=42 x2=335 y2=62 stroke=#f87171 stroke-width=2
  Body rect:  x=310 y=62 width=50 height=94 fill=#2a0d0d stroke=#f87171 stroke-width=2 rx=2
  Lower wick: x1=335 y1=156 x2=335 y2=176 stroke=#f87171 stroke-width=2
  Top label:  x=335 y=34 text-anchor=middle fill=#f87171 font-size=10 font-weight=bold "Bearish (Red)"

CENTER LABELS — ALL between x=160 and x=290, stacked 28px apart:
  "High (upper wick)"   x=225 y=50  text-anchor=middle fill=#9ca3af font-size=9
  "Open / Close"        x=225 y=78  text-anchor=middle fill=#9ca3af font-size=9
  "Close / Open"        x=225 y=150 text-anchor=middle fill=#9ca3af font-size=9
  "Low (lower wick)"    x=225 y=183 text-anchor=middle fill=#9ca3af font-size=9

CONNECTOR LINES (thin grey, dashed, connecting center labels to candle bodies):
  x1=175 y1=78  x2=140 y2=78  stroke=#374151 stroke-width=1 stroke-dasharray=3  (→ green body top)
  x1=275 y1=78  x2=310 y2=78  stroke=#374151 stroke-width=1 stroke-dasharray=3  (→ red body top)
  x1=175 y1=150 x2=140 y2=150 stroke=#374151 stroke-width=1 stroke-dasharray=3  (→ green body bottom)
  x1=275 y1=150 x2=310 y2=150 stroke=#374151 stroke-width=1 stroke-dasharray=3  (→ red body bottom)
  x1=195 y1=50  x2=115 y2=50  stroke=#374151 stroke-width=1 stroke-dasharray=3  (→ top wick)
  x1=195 y1=183 x2=115 y2=176 stroke=#374151 stroke-width=1 stroke-dasharray=3  (→ bottom wick)

Footer: "Green = buyers dominated that candle | Red = sellers dominated | Body size = conviction"{simplify}"""

        if "head" in tl or "shoulder" in tl:
            return f"""Create an SVG Head and Shoulders pattern diagram. Title: "{title}"

EXACT COORDINATES:

Price polyline (the pattern shape):
points="30,175 80,140 120,152 170,105 220,150 270,138 310,178"
stroke=#60a5fa stroke-width=2 fill=none

PEAKS AND TROUGHS — labels ABOVE peaks, BELOW troughs:
Left shoulder peak:  cx=80  cy=140 r=5 fill=#f87171  label "L. Shoulder" x=68  y=130 fill=#f87171 font-size=9
Left trough:         cx=120 cy=152 r=4 fill=#6b7280
Head peak:           cx=170 cy=105 r=6 fill=#f87171  label "Head"        x=158 y=95  fill=#f87171 font-size=10 font-weight=bold
Right trough:        cx=220 cy=150 r=4 fill=#6b7280
Right shoulder peak: cx=270 cy=138 r=5 fill=#f87171  label "R. Shoulder" x=258 y=128 fill=#f87171 font-size=9
Breakdown point:     cx=310 cy=178 r=5 fill=#fbbf24

NECKLINE: x1=120 y1=152 x2=380 y2=155 stroke=#a78bfa stroke-width=1.5 stroke-dasharray=4
Label "Neckline" x=385 y=153 fill=#a78bfa font-size=9

BREAKDOWN ARROW (red, pointing down): at x=310 from y=178 to y=200
Sell label: x=320 y=195 fill=#f87171 font-size=9 font-weight=bold "SELL SIGNAL"

Footer: "Neckline break = entry signal. Stop above right shoulder. Target = head height below neckline."{simplify}"""

        if "double" in tl and "bottom" in tl:
            return f"""Create an SVG Double Bottom (W pattern) diagram. Title: "{title}"

EXACT COORDINATES:

Price polyline:
points="30,80 80,150 130,100 180,150 230,75 310,60 400,45"
stroke=#60a5fa stroke-width=2 fill=none

LABELS — alternating above/below with 14px minimum gap:
Bottom 1: cx=80  cy=150 r=6 fill=#fbbf24  label "Bottom 1" x=55  y=168 fill=#fbbf24 font-size=9
Peak:     cx=130 cy=100 r=4 fill=#9ca3af
Bottom 2: cx=180 cy=150 r=6 fill=#fbbf24  label "Bottom 2" x=155 y=168 fill=#fbbf24 font-size=9
Breakout: cx=230 cy=75  r=6 fill=#34d399  label "Breakout" x=238 y=68  fill=#34d399 font-size=9 font-weight=bold

RESISTANCE LINE: x1=30 y1=100 x2=450 y2=100 stroke=#f87171 stroke-width=1.5 stroke-dasharray=4
Label "Resistance" x=455 y=98 text-anchor=end fill=#f87171 font-size=9

BUY ARROW (green, pointing up): at x=230 from y=75 up to y=50
Label "BUY SIGNAL" x=240 y=48 fill=#34d399 font-size=9 font-weight=bold

MEASURED MOVE TARGET:
Target line: x1=230 y1=50 x2=450 y2=50 stroke=#34d399 stroke-width=1 stroke-dasharray=2
Label "Target" x=455 y=48 text-anchor=end fill=#34d399 font-size=9

Footer: "Two equal lows = strong support. Break above resistance = buy signal."{simplify}"""

        if "double" in tl and "top" in tl:
            return f"""Create an SVG Double Top (M pattern) diagram. Title: "{title}"

EXACT COORDINATES:

Price polyline:
points="30,150 80,80 130,130 180,80 230,155 310,170 400,185"
stroke=#60a5fa stroke-width=2 fill=none

Top 1: cx=80  cy=80  r=6 fill=#fbbf24  label "Top 1"   x=68  y=70  fill=#fbbf24 font-size=9
Trough: cx=130 cy=130 r=4 fill=#9ca3af
Top 2: cx=180 cy=80  r=6 fill=#fbbf24  label "Top 2"   x=168 y=70  fill=#fbbf24 font-size=9
Breakdown: cx=230 cy=155 r=6 fill=#f87171 label "Breakdown" x=238 y=165 fill=#f87171 font-size=9

SUPPORT LINE: x1=30 y1=130 x2=450 y2=130 stroke=#34d399 stroke-width=1.5 stroke-dasharray=4
Label "Neckline Support" x=455 y=128 text-anchor=end fill=#34d399 font-size=9

SELL ARROW (red, pointing down): at x=230 from y=155 down to y=185
Label "SELL SIGNAL" x=240 y=200 fill=#f87171 font-size=9 font-weight=bold

Footer: "Two equal highs = strong resistance. Break below neckline = sell signal."{simplify}"""

        if "flag" in tl or "pennant" in tl:
            return f"""Create an SVG Bull Flag pattern diagram. Title: "{title}"

EXACT COORDINATES:

POLE (strong vertical surge): x1=80 y1=180 x2=80 y2=65 stroke=#34d399 stroke-width=3
Label "Pole" x=88 y=130 fill=#34d399 font-size=9

FLAG (parallel channel sloping down):
Upper channel: points="80,65 160,75 200,82" stroke=#60a5fa stroke-width=1.5 fill=none stroke-dasharray=3
Lower channel: points="80,90 160,100 200,107" stroke=#60a5fa stroke-width=1.5 fill=none stroke-dasharray=3
Fill between: polygon points="80,65 160,75 200,82 200,107 160,100 80,90" fill=#60a5fa fill-opacity=0.08

BREAKOUT ARROW (green, strong): from x=200,y=82 pointing up-right to x=280,y=45
polyline points="200,82 280,45" stroke=#34d399 stroke-width=2.5
Arrow head at (280,45) pointing up-right

MEASURED MOVE TARGET:
Height of pole = 115px. Target is same distance above breakout.
Target line: x1=200 y1=45 x2=420 y2=45 stroke=#34d399 stroke-width=1 stroke-dasharray=3
Label "Target (equal to pole)" x=405 y=40 fill=#34d399 font-size=9

Labels:
"Flag Channel" x=150 y=118 text-anchor=middle fill=#60a5fa font-size=9
"Breakout" x=240 y=72 fill=#34d399 font-size=9 font-weight=bold

Footer: "Pole = impulse move. Flag = consolidation. Breakout = entry. Target = pole height."{simplify}"""

        # Generic pattern fallback
        return f"""Create an SVG chart pattern diagram. Title: "{title}"

CONTEXT: {intent}

DRAW THIS EXACTLY:
1. Title "{title}" at standard position
2. A price polyline showing the pattern shape clearly — peaks and troughs clearly visible
3. Label EACH key point (peaks, troughs, necklines) with text ABOVE or BELOW the point
   — labels above peaks, labels below troughs, minimum 16px vertical gap between any two labels
4. A horizontal dashed line at the key breakout/breakdown level labeled "Breakout Level"
5. Entry circle (yellow, r=6) at the signal point with label "Entry" offset right by 12px
6. Green or red arrow showing expected direction after pattern completes
7. "Target" dashed line showing the measured move objective
Footer: "Wait for CONFIRMATION (breakout candle close) before entering"{simplify}"""

    # ── MARKET STRUCTURE ─────────────────────────────────────────────────────
    if classification == "structure":

        if "order block" in tl:
            return f"""Create an SVG Order Block diagram. Title: "{title}"

EXACT COORDINATES:

1. Background + Title (standard)

2. ORDER BLOCK CANDLE (the last bearish candle before the impulse):
   rect x=60 y=118 width=28 height=42 fill=#2a0d0d stroke=#f87171 stroke-width=1.5 rx=2
   Label "Order Block" x=74 y=172 text-anchor=middle fill=#f87171 font-size=9

3. DISPLACEMENT (strong bullish impulse up from OB):
   polyline points="88,135 140,100 190,70 240,50"
   stroke=#34d399 stroke-width=3 fill=none
   Label "Displacement" x=170 y=65 text-anchor=middle fill=#34d399 font-size=9

4. RETURN TO OB (price retraces back — dashed blue):
   polyline points="240,50 290,75 330,100 360,118"
   stroke=#60a5fa stroke-width=1.5 fill=none stroke-dasharray=5
   Label "Return to OB" x=330 y=90 fill=#60a5fa font-size=9

5. ENTRY ZONE AT OB:
   rect x=345 y=115 width=50 height=42 fill=#34d399 fill-opacity=0.15 stroke=#34d399 stroke-width=1 stroke-dasharray=3 rx=2
   Circle cx=370 cy=136 r=6 fill=#fbbf24
   Label "Entry" x=400 y=134 fill=#fbbf24 font-size=9 font-weight=bold

6. EXPECTED MOVE UP (green arrow):
   polyline points="370,130 400,100 430,75"
   stroke=#34d399 stroke-width=2 fill=none
   Arrowhead at (430,75)

Footer: "Last bearish candle before impulse = Order Block. Enter when price returns. Stop below OB."{simplify}"""

        if "liquidity" in tl:
            return f"""Create an SVG Liquidity Sweep diagram. Title: "{title}"

EXACT COORDINATES:

1. Background + Title (standard)

2. EQUAL LOWS (sell-side liquidity pool):
   Three equal-height candle wicks touching y=160:
   x1=80  y1=140 x2=80  y2=162 stroke=#6b7280 stroke-width=2
   x1=130 y1=138 x2=130 y2=162 stroke=#6b7280 stroke-width=2
   x1=180 y1=135 x2=180 y2=162 stroke=#6b7280 stroke-width=2
   Equal lows line: x1=60 y1=162 x2=450 y2=162 stroke=#f87171 stroke-width=1 stroke-dasharray=4
   Label "Sell-Side Liquidity" x=240 y=158 text-anchor=middle fill=#f87171 font-size=9

3. LIQUIDITY SWEEP (price dips BELOW the equal lows briefly):
   polyline points="180,135 220,155 240,172 260,155 290,125"
   stroke=#f87171 stroke-width=2.5 fill=none
   Red shaded spike zone: rect x=225 y=160 width=40 height=18 fill=#f87171 fill-opacity=0.2 rx=2
   Label "Swept!" x=245 y=193 text-anchor=middle fill=#f87171 font-size=9 font-weight=bold

4. REJECTION AND RECOVERY:
   polyline points="290,125 330,105 370,80 420,60"
   stroke=#34d399 stroke-width=2.5 fill=none
   Circle cx=290 cy=125 r=7 fill=none stroke=#34d399 stroke-width=2
   Label "Entry After Sweep" x=298 y=120 fill=#34d399 font-size=9

5. STOP LOSS MARKERS (SVG text elements INSIDE the SVG, above footer):
   <text x="232" y="182" fill="#f87171" font-size="10" font-family="Inter, sans-serif">×</text>
   <text x="244" y="182" fill="#f87171" font-size="10" font-family="Inter, sans-serif">×</text>
   <text x="256" y="182" fill="#f87171" font-size="10" font-family="Inter, sans-serif">×</text>
   <text x="244" y="193" text-anchor="middle" fill="#f87171" font-size="8" font-family="Inter, sans-serif">Stop Losses</text>

6. ALL labels must be INSIDE the SVG — nothing after </svg>

Footer text (inside SVG at y=213): "Price sweeps stops below lows then reverses — enter after recovery"{simplify}"""

        if any(k in tl for k in ["bos", "choch", "break of structure", "change of character", "market structure"]):
            return f"""Create an SVG Market Structure (BOS/CHoCH) diagram. Title: "{title}"

EXACT COORDINATES — LABELS ALTERNATE ABOVE/BELOW TO PREVENT OVERLAP:

Price polyline (uptrend with BOS):
points="25,190 70,165 100,175 145,140 178,153 218,118 252,132 292,98 315,112 340,88 380,100 420,72"
stroke=#60a5fa stroke-width=2 fill=none

SWING POINTS (circles r=5, labels STRICTLY alternating ABOVE peaks, BELOW troughs):
HL1: cx=70  cy=165 r=5 fill=#fbbf24  label x=58  y=180 fill=#fbbf24 font-size=9 "HL"   ← BELOW
HH1: cx=145 cy=140 r=5 fill=#34d399  label x=133 y=130 fill=#34d399 font-size=9 "HH"   ← ABOVE
HL2: cx=178 cy=153 r=5 fill=#fbbf24  label x=166 y=168 fill=#fbbf24 font-size=9 "HL"   ← BELOW
HH2: cx=218 cy=118 r=5 fill=#34d399  label x=206 y=108 fill=#34d399 font-size=9 "HH"   ← ABOVE
HL3: cx=252 cy=132 r=5 fill=#fbbf24  label x=240 y=147 fill=#fbbf24 font-size=9 "HL"   ← BELOW
BOS: cx=292 cy=98  r=6 fill=#a78bfa  label x=298 y=92  fill=#a78bfa font-size=9 font-weight=bold "BOS ↑"  ← ABOVE-RIGHT
HL4: cx=315 cy=112 r=5 fill=#fbbf24  label x=303 y=127 fill=#fbbf24 font-size=9 "HL"   ← BELOW
Entry: cx=340 cy=112 r=6 fill=#fbbf24

BOS REFERENCE LINE (where HH2 was broken):
x1=218 y1=118 x2=460 y2=118 stroke=#a78bfa stroke-width=1 stroke-dasharray=4
Label "Previous HH" x=455 y=114 text-anchor=end fill=#a78bfa font-size=8

ENTRY LABEL: x=350 y=110 fill=#fbbf24 font-size=9 "Entry"

SMALL LEGEND (y=175 and y=190 — 15px apart, left side x=25):
Green dot cx=32 cy=172 r=4 fill=#34d399  "= HH (Higher High)" x=40 y=175 fill=#9ca3af font-size=8
Yellow dot cx=32 cy=187 r=4 fill=#fbbf24 "= HL (Higher Low)"  x=40 y=190 fill=#9ca3af font-size=8

Footer: "BOS = trend continuation confirmed. Enter at next HL after BOS."{simplify}"""

        # Generic structure (support/resistance)
        return f"""Create an SVG support and resistance diagram. Title: "{title}"

EXACT COORDINATES:

1. Background + Title (standard)

2. Price polyline oscillating between two levels:
   points="25,155 70,128 100,160 140,118 175,155 215,115 255,152 295,112 335,150 375,108 420,148 455,105"
   stroke=#60a5fa stroke-width=2 fill=none

3. RESISTANCE LINE: x1=25 y1=112 x2=460 y2=112 stroke=#f87171 stroke-width=2 stroke-dasharray=6
   Label "RESISTANCE" x=30 y=106 fill=#f87171 font-size=10 font-weight=bold

4. SUPPORT LINE: x1=25 y1=158 x2=460 y2=158 stroke=#34d399 stroke-width=2 stroke-dasharray=6
   Label "SUPPORT" x=30 y=176 fill=#34d399 font-size=10 font-weight=bold

5. REJECTION ARROWS at resistance (red, pointing down): at x=140, x=215, x=295
   Each: x1=xpos y1=112 x2=xpos y2=100 stroke=#f87171 stroke-width=1.5 — arrowhead at top

6. BOUNCE ARROWS at support (green, pointing up): at x=100, x=175, x=255
   Each: x1=xpos y1=158 x2=xpos y2=146 stroke=#34d399 stroke-width=1.5 — arrowhead at top

7. Entry circle: cx=420 cy=148 r=6 fill=#fbbf24
   Label "Buy here" x=430 y=146 fill=#fbbf24 font-size=9

Footer: "Support = buy zone. Resistance = sell zone. Role reversal: broken support becomes resistance."{simplify}"""

    # ── CONCEPT (default) ────────────────────────────────────────────────────
    return f"""Create an SVG educational diagram for the forex concept: "{title}"

CONTEXT: {intent}

INSTRUCTIONS:
1. Title "{title}" at standard position (x=240 y=16 purple)
2. Choose the MOST APPROPRIATE visual for this concept:
   - CALCULATION/FORMULA → purple highlighted box at y=38-78 with formula text, worked example box below
   - COMPARISON → two or three side-by-side columns with colored headers and bullet points
   - PROCESS/STEPS → numbered flow boxes connected by arrows (top to bottom or left to right)
   - MARKET CONCEPT → simple annotated price chart with entry/exit markers
3. SPACING RULES — strictly enforced:
   - All text labels minimum 14px apart vertically
   - No text outside x=20 to x=460 boundary
   - All text inside y=22 to y=208 boundary
4. Use green (#34d399) for positive outcomes, red (#f87171) for negative, yellow (#fbbf24) for highlights
5. Maximum 15 elements total (not counting background)
6. Footer: one sentence key takeaway for this specific concept{simplify}"""


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
- Minimum 6 elements, maximum 20 elements

CRITICAL — CONTENT CONTAINMENT:
- ALL elements (text, shapes, lines) MUST be placed INSIDE <svg>...</svg> tags
- NEVER output any characters, labels, or text AFTER the closing </svg> tag
- Special symbols like × must use <text> SVG elements with explicit x/y coordinates
- Keep all content within y=10 to y=215 (footer at y=215 max)
- Overlapping labels: if two labels share x±30px range, offset vertically by minimum 14px"""


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

        user_id = _user_get(current_user, "id", 0)
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

        user_id = _user_get(current_user, "id", 0)
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

        user_id = _user_get(current_user, "id", 0)
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

        # DISTINCT ON question prevents duplicate questions from multiple seed runs.
        # LIMIT 5 enforces max 5 questions per lesson — standard across all levels.
        questions = await database.fetch_all(
            """SELECT DISTINCT ON (question) id, question, option_a, option_b, option_c, option_d,
                      correct_answer, explanation, topic_slug
               FROM lesson_quizzes
               WHERE lesson_id=:lid
               ORDER BY question, id
               LIMIT 5""",
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
        caller   = _user_get(current_user, "id", 0)
        is_admin = _user_get(current_user, "is_admin", False)
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
        completed_lessons = sum(1 for p in (rows or []) if p and p["completed"])

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
        caller   = _user_get(current_user, "id", 0)
        is_admin = _user_get(current_user, "is_admin", False)
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
        caller   = _user_get(current_user, "id", 0)
        is_admin = _user_get(current_user, "is_admin", False)
        if caller != user_id and not is_admin:
            raise HTTPException(403, "Forbidden")

        profile = await database.fetch_one(
            "SELECT first_academy_visit, weak_topics FROM user_learning_profile WHERE user_id=:uid",
            {"uid": user_id}
        )
        first_visit = (not profile) or bool((dict(profile).get("first_academy_visit", True) if profile else True))

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
            weak_raw = (dict(profile).get("weak_topics", "[]") if profile else "[]")
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
        user_id = _user_get(current_user, "id", 0)
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
        user_id = _user_get(current_user, "id", 0)
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
        user_id = _user_get(current_user, "id", 0)
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
        user_id = _user_get(current_user, "id", 0)
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
        content_preview = ((lesson["content"] if lesson and "content" in dict(lesson) else "") or "")[:500]
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
        level = (lesson["level_name"] if lesson else "Beginner").lower()
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
            cur_weak   = _parse_json((existing["weak_topics"] if existing else "[]"))
            cur_strong = _parse_json((existing["strong_topics"] if existing else "[]"))
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
