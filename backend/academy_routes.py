"""
Pipways Trading Academy — Standalone Router v1.0
Responsibilities:
  1. GET  /academy.html     → serve academy.html (primary, mirrors dashboard.html)
  2. GET  /academy          → 301 redirect to /academy.html
  3. All  /learning/*       → full LMS API (moved from learning.py / main.py)
  4. AI Diagram Generation System — Fully Integrated
"""

import os
import json
import re
import xml.etree.ElementTree as ET
import asyncio
import traceback
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx

from .security import get_current_user
from .database import database

router = APIRouter()

def _user_get(user, key, default=None):
    """Safe attribute access for both dict and asyncpg Record objects."""
    if user is None:
        return default
    try:
        return user[key]
    except (KeyError, TypeError):
        try:
            return user.get(key, default)
        except AttributeError:
            return default

# ══════════════════════════════════════════════════════════════════════════════
# AI DIAGRAM GENERATION SYSTEM — INTEGRATED
# ══════════════════════════════════════════════════════════════════════════════

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_DIAGRAM_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

COLOR_SCHEME = {
    "background": "#0d1117",
    "bullish": "#34d399",
    "bearish": "#f87171",
    "accent": "#a78bfa",
    "entry": "#fbbf24",
    "text": "#e5e7eb",
    "subtext": "#9ca3af",
    "grid": "#374151",
    "support": "#22c55e",
    "resistance": "#ef4444"
}

DIAGRAM_TYPES = {
    "price_action": "Candlestick charts, trend lines, support/resistance with entry/exit points",
    "risk_management": "Risk/reward ratios, position sizing, stop loss visualization",
    "indicator": "RSI, MACD, Moving Average panels with overbought/oversold zones",
    "pattern": "Chart patterns: Head & Shoulders, Double Tops, Flags, Triangles",
    "structure": "Order blocks, liquidity pools, market structure breaks",
    "concept": "Abstract concepts: correlation, session times, market hierarchy"
}

@dataclass
class DiagramContext:
    concept: str
    diagram_type: str
    elements: List[str]
    values: Dict[str, str]
    trend_direction: Optional[str] = None
    timeframe: Optional[str] = None


class LessonClassifier:
    """Rule-based lesson classification engine"""
    
    KEYWORD_PATTERNS = {
        "price_action": [
            r"candlestick", r"support", r"resistance", r"trend", r"swing", r"pullback",
            r"higher high", r"lower low", r"bounce", r"rejection", r"breakout",
            r"consolidation", r"range", r"wick", r"body", r"engulfing", r"pin bar"
        ],
        "risk_management": [
            r"risk", r"reward", r"r:r", r"stop loss", r"take profit", r"position size",
            r"lot", r"leverage", r"margin", r"drawdown", r"1-2%", r"portfolio heat",
            r"expectancy", r"profit factor", r"consecutive loss"
        ],
        "indicator": [
            r"rsi", r"macd", r"moving average", r"ema", r"sma", r"adx", r"bollinger",
            r"stochastic", r"overbought", r"oversold", r"divergence", r"crossover",
            r"momentum", r"oscillator", r"golden cross", r"death cross"
        ],
        "pattern": [
            r"pattern", r"head and shoulders", r"double top", r"double bottom",
            r"flag", r"pennant", r"triangle", r"wedge", r"rectangle", r"cup and handle",
            r"ascending", r"descending", r"symmetrical", r"breakout", r"reversal"
        ],
        "structure": [
            r"order block", r"liquidity", r"sweep", r"inducement", r"break of structure",
            r"bos", r"choch", r"fvg", r"fair value gap", r"imbalance", r"mitigation",
            r"institutional", r"smart money", r"footprint"
        ],
        "concept": [
            r"session", r"correlation", r"spread", r"pip", r"lot", r"leverage",
            r"participant", r"central bank", r"market structure", r"timeframe",
            r"confluence", r"fundamental"
        ]
    }
    
    def classify(self, title: str, content: str) -> str:
        text = f"{title} {content}".lower()
        scores = {}
        
        for diagram_type, patterns in self.KEYWORD_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in text)
            title_score = sum(2 for pattern in patterns if pattern in title.lower())
            scores[diagram_type] = score + title_score
        
        best_match = max(scores, key=scores.get)
        return best_match if scores[best_match] > 0 else "concept"


class ContentExtractor:
    """Extract structured context from lesson content"""
    
    PRICE_PATTERN = r'(\d+\.\d{3,})'
    PIP_PATTERN = r'(\d+)\s*pips?'
    PERCENTAGE_PATTERN = r'(\d+(?:\.\d+)?)%'
    RATIO_PATTERN = r'(\d+):\s*(\d+)'
    
    def extract(self, title: str, content: str) -> DiagramContext:
        concept_match = re.search(r'##\s*(.+?)(?=\n|$)', content)
        if concept_match:
            concept = concept_match.group(1).strip()
        else:
            sentences = re.split(r'(?<=[.!?])\s+', content)
            concept = sentences[0][:120] if sentences else title
        
        prices = re.findall(self.PRICE_PATTERN, content)
        pips = re.findall(self.PIP_PATTERN, content, re.IGNORECASE)
        percentages = re.findall(self.PERCENTAGE_PATTERN, content)
        ratios = re.findall(self.RATIO_PATTERN, content)
        
        values = {}
        
        if prices:
            for i, price in enumerate(prices[:3]):
                context = self._get_value_context(content, price)
                if any(word in context for word in ['entry', 'buy', 'sell', 'at']):
                    values['entry'] = price
                elif any(word in context for word in ['stop', 'sl', 'loss']):
                    values['stop_loss'] = price
                elif any(word in context for word in ['target', 'tp', 'profit', 'take']):
                    values['take_profit'] = price
        
        if ratios:
            values['risk_reward'] = f"{ratios[0][0]}:{ratios[0][1]}"
        
        if pips:
            values['pip_distance'] = pips[0]
        
        trend = None
        if any(word in content.lower() for word in ['uptrend', 'bullish', 'buy', 'support', 'higher']):
            trend = 'bullish'
        elif any(word in content.lower() for word in ['downtrend', 'bearish', 'sell', 'resistance', 'lower']):
            trend = 'bearish'
        
        elements = []
        element_keywords = {
            'Entry': ['entry', 'buy at', 'sell at', 'open position'],
            'Stop Loss': ['stop loss', 'stop', 'sl'],
            'Take Profit': ['take profit', 'target', 'tp'],
            'Support': ['support level', 'support zone'],
            'Resistance': ['resistance level', 'resistance zone'],
            'Trend Line': ['trend line', 'trendline'],
            'Moving Average': ['moving average', 'ema', 'sma'],
            'RSI': ['rsi', 'relative strength'],
            'MACD': ['macd'],
            'Candlestick': ['candle', 'wick', 'body']
        }
        
        for element, keywords in element_keywords.items():
            if any(kw in content.lower() for kw in keywords):
                elements.append(element)
        
        classifier = LessonClassifier()
        diagram_type = classifier.classify(title, content)
        
        return DiagramContext(
            concept=concept,
            diagram_type=diagram_type,
            elements=elements,
            values=values,
            trend_direction=trend
        )
    
    def _get_value_context(self, content: str, value: str, window: int = 50) -> str:
        idx = content.find(value)
        if idx == -1:
            return ""
        start = max(0, idx - window)
        end = min(len(content), idx + len(value) + window)
        return content[start:end].lower()


class PromptTemplateEngine:
    """Generate structured prompts based on diagram type"""
    
    def build_prompt(self, context: DiagramContext) -> Tuple[str, str]:
        type_template = self._get_type_template(context)
        system_prompt = self._get_system_prompt()
        
        user_prompt = f"""Generate a professional SVG diagram for a Forex trading lesson.

CONCEPT: {context.concept}

DIAGRAM TYPE: {context.diagram_type}

KEY ELEMENTS: {', '.join(context.elements) if context.elements else 'Basic chart structure'}

TREND: {context.trend_direction or 'neutral'}

VALUES: {json.dumps(context.values, indent=2) if context.values else 'Use realistic example values'}

SPECIFIC REQUIREMENTS:
{self._get_specific_requirements(context)}

OUTPUT: Return ONLY the SVG code. No markdown, no explanation, no code fences."""
        
        return system_prompt, user_prompt
    
    def _get_system_prompt(self) -> str:
        return f"""You are an expert SVG diagram generator for financial education. Your task is to create clean, professional SVG diagrams for Forex trading lessons.

STRICT RULES:
1. Return ONLY SVG code - no markdown, no text, no explanation
2. SVG must start with <svg and end with </svg>
3. Use dark theme with these EXACT colors:
   - Background: {COLOR_SCHEME['background']}
   - Bullish/Profit: {COLOR_SCHEME['bullish']}
   - Bearish/Loss: {COLOR_SCHEME['bearish']}
   - Labels/Title: {COLOR_SCHEME['accent']}
   - Entry Points: {COLOR_SCHEME['entry']}
   - Text: {COLOR_SCHEME['text']}
   - Subtext: {COLOR_SCHEME['subtext']}
   - Grid: {COLOR_SCHEME['grid']}
4. Max width: 480px, height: 200px (viewBox="0 0 480 200")
5. Font: system-ui, sans-serif
6. Include clear labels with text elements
7. Professional, minimalist style
8. Educational focus - make concepts visually clear

SVG STRUCTURE:
- <rect> for background and zones
- <line> or <polyline> for price action
- <circle> for entry/exit points
- <text> for labels (font-size 9-12)
- <path> for complex shapes

DO NOT include:
- JavaScript
- CSS animations
- External images
- Interactive elements"""
    
    def _get_specific_requirements(self, context: DiagramContext) -> str:
        templates = {
            "price_action": self._price_action_template,
            "risk_management": self._risk_management_template,
            "indicator": self._indicator_template,
            "pattern": self._pattern_template,
            "structure": self._structure_template,
            "concept": self._concept_template
        }
        return templates.get(context.diagram_type, self._concept_template)(context)
    
    def _price_action_template(self, context: DiagramContext) -> str:
        return """
Price Action Chart Requirements:
- Show candlestick or line chart showing price movement
- Mark entry point with yellow circle
- Show stop loss (red line below entry for long, above for short)
- Show take profit (green line)
- Label with realistic price levels
- Include brief trend indication
- Show 1-2 support/resistance levels if relevant
"""
    
    def _risk_management_template(self, context: DiagramContext) -> str:
        values = context.values
        rr = values.get('risk_reward', '1:2')
        return f"""
Risk Management Visualization:
- Split view: Risk zone (red) vs Reward zone (green)
- Show R:R ratio prominently ({rr})
- Dollar/pip amounts labeled clearly
- Position size calculation example if space permits
- Account percentage indicator (1-2%)
- Visual balance between risk and reward areas
"""
    
    def _indicator_template(self, context: DiagramContext) -> str:
        indicator = "RSI" if "RSI" in context.elements else "MACD"
        return f"""
Indicator Panel Requirements ({indicator}):
- Show indicator line(s) in main color
- Mark overbought zone (70+) in red tint
- Mark oversold zone (30-) in green tint
- Show current value marker
- Midline at 50 (gray)
- Simple histogram or line representation
- Clean, readable scale
"""
    
    def _pattern_template(self, context: DiagramContext) -> str:
        return """
Chart Pattern Requirements:
- Clear pattern structure (Head & Shoulders, Double Top, Flag, etc.)
- Label key points (Left Shoulder, Head, Right Shoulder, Neckline)
- Entry trigger point marked
- Target projection based on pattern height
- Breakout/breakdown point highlighted
"""
    
    def _structure_template(self, context: DiagramContext) -> str:
        return """
Market Structure Diagram:
- Show price swing structure (highs and lows)
- Mark order block zone (rectangle)
- Show liquidity sweep (wick beyond level)
- Break of Structure (BOS) indicator
- Return to order block (mitigation)
- Clean labeling of each phase
"""
    
    def _concept_template(self, context: DiagramContext) -> str:
        return """
Concept Diagram:
- Simplified visual representation
- Key components labeled clearly
- Flow or hierarchy if applicable
- Minimalist design
- Focus on clarity over complexity
"""


class SVGValidator:
    """Validate generated SVG for security and structure"""
    
    MAX_SIZE = 20000
    ALLOWED_TAGS = {
        'svg', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
        'path', 'text', 'g', 'defs', 'linearGradient', 'stop', 'title', 'desc',
        'animate', 'animateTransform'  # Allow SMIL animations for loaders
    }
    FORBIDDEN_PATTERNS = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
        r'href\s*=\s*["\'][^"\']*javascript',
        r'xlink:href',
        r'foreignObject',
        r'embed',
        r'iframe'
    ]
    
    def validate(self, svg: str) -> Tuple[bool, Optional[str]]:
        if not svg or not svg.strip():
            return False, "Empty SVG"
        
        svg = svg.strip()
        
        if not svg.startswith('<svg'):
            return False, "Does not start with <svg"
        
        if not svg.endswith('</svg>'):
            return False, "Does not end with </svg>"
        
        if len(svg) > self.MAX_SIZE:
            return False, f"SVG too large ({len(svg)} > {self.MAX_SIZE})"
        
        svg_lower = svg.lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, svg_lower):
                return False, f"Forbidden pattern detected: {pattern}"
        
        try:
            root = ET.fromstring(svg)
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag not in self.ALLOWED_TAGS:
                    return False, f"Disallowed tag: {tag}"
        except ET.ParseError as e:
            return False, f"XML parsing error: {str(e)}"
        
        if 'viewBox' not in svg and ('width' not in svg or 'height' not in svg):
            return False, "Missing viewBox or width/height"
        
        return True, None


class DiagramGenerator:
    """Main orchestrator for diagram generation"""
    
    def __init__(self):
        self.classifier = LessonClassifier()
        self.extractor = ContentExtractor()
        self.templater = PromptTemplateEngine()
        self.validator = SVGValidator()
        self.max_retries = 2
    
    async def generate(self, title: str, content: str, lesson_id: int) -> Tuple[str, bool]:
        context = self.extractor.extract(title, content)
        system_prompt, user_prompt = self.templater.build_prompt(context)
        
        for attempt in range(self.max_retries + 1):
            try:
                svg = await self._call_ai(system_prompt, user_prompt, attempt)
                
                if svg:
                    svg = self._clean_svg(svg)
                    is_valid, error = self.validator.validate(svg)
                    
                    if is_valid:
                        return svg, True
                    else:
                        print(f"[DIAGRAM] Validation failed (attempt {attempt+1}): {error}")
                        if attempt < self.max_retries:
                            user_prompt += "\n\nSIMPLIFY: Create a simpler diagram with fewer elements."
                
            except Exception as e:
                print(f"[DIAGRAM] Generation error (attempt {attempt+1}): {e}")
                if attempt == self.max_retries:
                    break
        
        return self._generate_fallback(context), False
    
    async def _call_ai(self, system: str, user: str, attempt: int) -> Optional[str]:
        if not OPENROUTER_API_KEY:
            print("[DIAGRAM] No API key configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=45) as client:
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
                        "max_tokens": 2500,
                        "temperature": 0.2 if attempt == 0 else 0.1,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    }
                )
                
                if res.status_code != 200:
                    print(f"[DIAGRAM] API error {res.status_code}: {res.text[:200]}")
                    return None
                
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                
                svg_match = re.search(r'<svg[\s\S]*?</svg>', content)
                if svg_match:
                    return svg_match.group(0)
                
                return None
                
        except Exception as e:
            print(f"[DIAGRAM] API call failed: {e}")
            return None
    
    def _clean_svg(self, svg: str) -> str:
        svg = re.sub(r'```svg\s*', '', svg)
        svg = re.sub(r'```\s*$', '', svg)
        
        if 'xmlns=' not in svg:
            svg = svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
        
        svg = re.sub(r'>\s+<', '><', svg)
        return svg.strip()
    
    def _generate_fallback(self, context: DiagramContext) -> str:
        colors = COLOR_SCHEME
        return f'''<svg viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg" class="ac-svg-diagram">
  <rect width="480" height="200" fill="{colors['background']}" rx="8"/>
  <text x="240" y="80" text-anchor="middle" fill="{colors['accent']}" font-size="14" font-weight="bold">Diagram: {context.concept[:40]}</text>
  <text x="240" y="110" text-anchor="middle" fill="{colors['subtext']}" font-size="11">{context.diagram_type.replace('_', ' ').title()} Visualization</text>
  <rect x="180" y="130" width="120" height="30" fill="{colors['bullish']}" opacity="0.2" rx="4"/>
  <text x="240" y="150" text-anchor="middle" fill="{colors['bullish']}" font-size="10">Interactive Diagram Loading...</text>
</svg>'''

# Initialize singleton
diagram_generator = DiagramGenerator()

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

class DiagramResponse(BaseModel):
    lesson_id: int
    svg: str
    diagram_type: str
    generated: bool
    elements: List[str]

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
               GROUP BY level_id"""
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

# ── Locate academy.html ───────────────────────────────────────────────────────
_BASE = Path(__file__).parent

def _find_academy_html() -> Optional[Path]:
    candidates = [
        _BASE.parent / "frontend" / "static" / "academy.html",
        _BASE.parent / "static" / "academy.html",
        _BASE / "academy.html",
        _BASE / "academy (1).html",  # Handle uploaded filename
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

@router.get("/academy.html")
async def serve_academy(request: Request):
    p = _find_academy_html()
    if p:
        return FileResponse(str(p), media_type="text/html")
    raise HTTPException(
        status_code=404,
        detail="academy.html not found. Place it in frontend/static/academy.html or static/academy.html."
    )

@router.get("/academy")
async def academy_clean_url_redirect():
    return RedirectResponse(url="/academy.html", status_code=301)

# ══════════════════════════════════════════════════════════════════════════════
# LMS API — /learning/*
# ══════════════════════════════════════════════════════════════════════════════

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
            """SELECT l.id, l.title, l.content, l.order_index, l.module_id, l.diagram_svg,
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

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM GENERATION ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/learning/lesson/{lesson_id}/diagram", response_model=DiagramResponse)
async def get_lesson_diagram(
    lesson_id: int, 
    force_regenerate: bool = Query(False, description="Force regeneration even if cached"),
    current_user=Depends(get_current_user)
):
    """
    Get or generate diagram for a lesson.
    Returns cached SVG if available, otherwise generates new one asynchronously.
    """
    try:
        lesson = await database.fetch_one(
            "SELECT id, title, content, diagram_svg, diagram_status FROM learning_lessons WHERE id=:lid",
            {"lid": lesson_id}
        )
        if not lesson:
            raise HTTPException(404, "Lesson not found")
        
        # Return cached if available and valid
        if not force_regenerate and lesson.get("diagram_svg") and lesson.get("diagram_status") == "complete":
            context = ContentExtractor().extract(lesson["title"], lesson["content"] or "")
            return DiagramResponse(
                lesson_id=lesson_id,
                svg=lesson["diagram_svg"],
                diagram_type=context.diagram_type,
                generated=False,
                elements=context.elements
            )
        
        # If currently generating, return status
        if lesson.get("diagram_status") == "generating" and not force_regenerate:
            return DiagramResponse(
                lesson_id=lesson_id,
                svg=_get_generating_placeholder(),
                diagram_type="loading",
                generated=False,
                elements=["Generating..."]
            )
        
        # Mark as generating
        await database.execute(
            "UPDATE learning_lessons SET diagram_status='generating' WHERE id=:lid",
            {"lid": lesson_id}
        )
        
        # Generate diagram
        svg, success = await diagram_generator.generate(
            lesson["title"], 
            lesson.get("content", ""), 
            lesson_id
        )
        
        # Update database
        status = "complete" if success else "failed"
        await database.execute(
            """UPDATE learning_lessons 
               SET diagram_svg=:svg, diagram_status=:status, diagram_generated_at=NOW() 
               WHERE id=:lid""",
            {"lid": lesson_id, "svg": svg, "status": status}
        )
        
        context = ContentExtractor().extract(lesson["title"], lesson["content"] or "")
        
        return DiagramResponse(
            lesson_id=lesson_id,
            svg=svg,
            diagram_type=context.diagram_type,
            generated=True,
            elements=context.elements
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API ERROR] get_lesson_diagram: {e}", flush=True)
        await database.execute(
            "UPDATE learning_lessons SET diagram_status='failed' WHERE id=:lid",
            {"lid": lesson_id}
        )
        raise HTTPException(500, f"Diagram generation failed: {str(e)}")

def _get_generating_placeholder() -> str:
    return '''<svg viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg" class="ac-svg-diagram">
  <rect width="480" height="200" fill="#0d1117" rx="8"/>
  <circle cx="240" cy="100" r="20" fill="none" stroke="#7c3aed" stroke-width="3" stroke-dasharray="60" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" from="0 240 100" to="360 240 100" dur="1s" repeatCount="indefinite"/>
  </circle>
  <text x="240" y="140" text-anchor="middle" fill="#9ca3af" font-size="12">Generating diagram...</text>
</svg>'''

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
# ADMIN — Seed health + reseed + Diagram Status
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/admin/academy/status")
async def academy_status(current_user=Depends(get_current_user)):
    """Returns DB row counts for all academy tables."""
    try:
        r_lv = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_levels")
        r_mo = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_modules")
        r_le = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_lessons")
        r_qu = await database.fetch_one("SELECT COUNT(*) AS c FROM lesson_quizzes")
        r_dia = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_lessons WHERE diagram_status='complete'")
        levels  = r_lv["c"] if r_lv else 0
        modules = r_mo["c"] if r_mo else 0
        lessons = r_le["c"] if r_le else 0
        quizzes = r_qu["c"] if r_qu else 0
        diagrams = r_dia["c"] if r_dia else 0
        return {
            "levels":    levels,
            "modules":   modules,
            "lessons":   lessons,
            "quizzes":   quizzes,
            "diagrams_complete": diagrams,
            "is_seeded": levels > 0 and modules > 0 and lessons > 0,
            "orphaned":  levels > 0 and modules == 0,
        }
    except Exception as e:
        raise HTTPException(500, f"Status check failed: {e}")

@router.get("/admin/academy/diagram-status")
async def diagram_generation_status(current_user=Depends(get_current_user)):
    """Get statistics on diagram generation across all lessons"""
    is_admin = _user_get(current_user, "is_admin", False)
    if not is_admin:
        raise HTTPException(403, "Admin only")
    
    try:
        stats = await database.fetch_all("""
            SELECT 
                diagram_status,
                COUNT(*) as count
            FROM learning_lessons
            GROUP BY diagram_status
        """)
        
        total_lessons = await database.fetch_val("SELECT COUNT(*) FROM learning_lessons") or 0
        complete = sum(r["count"] for r in stats if r["diagram_status"] == "complete")
        
        return {
            "total_lessons": total_lessons,
            "complete": complete,
            "pending": sum(r["count"] for r in stats if r["diagram_status"] == "pending" or r["diagram_status"] is None),
            "generating": sum(r["count"] for r in stats if r["diagram_status"] == "generating"),
            "failed": sum(r["count"] for r in stats if r["diagram_status"] == "failed"),
            "completion_rate": round(complete / total_lessons * 100, 1) if total_lessons else 0,
            "breakdown": [dict(r) for r in stats]
        }
    except Exception as e:
        raise HTTPException(500, f"Status check failed: {e}")

@router.post("/admin/academy/regenerate-diagrams")
async def regenerate_all_diagrams(
    lesson_ids: Optional[List[int]] = None,
    current_user=Depends(get_current_user)
):
    """Admin endpoint to batch regenerate diagrams."""
    is_admin = _user_get(current_user, "is_admin", False)
    if not is_admin:
        raise HTTPException(403, "Admin only")
    
    try:
        if lesson_ids:
            rows = await database.fetch_all(
                "SELECT id, title, content FROM learning_lessons WHERE id = ANY(:ids)",
                {"ids": lesson_ids}
            )
        else:
            rows = await database.fetch_all(
                """SELECT id, title, content FROM learning_lessons 
                   WHERE diagram_status != 'complete' OR diagram_svg IS NULL
                   LIMIT 50"""
            )
        
        results = []
        for lesson in rows:
            try:
                svg, success = await diagram_generator.generate(
                    lesson["title"],
                    lesson.get("content", ""),
                    lesson["id"]
                )
                
                status = "complete" if success else "failed"
                await database.execute(
                    """UPDATE learning_lessons 
                       SET diagram_svg=:svg, diagram_status=:status, diagram_generated_at=NOW()
                       WHERE id=:lid""",
                    {"lid": lesson["id"], "svg": svg, "status": status}
                )
                
                results.append({
                    "lesson_id": lesson["id"],
                    "success": success,
                    "status": status
                })
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                results.append({
                    "lesson_id": lesson["id"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "processed": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(500, f"Batch regeneration failed: {e}")

@router.post("/admin/academy/reseed")
async def academy_reseed(current_user=Depends(get_current_user)):
    """Admin only. Wipes curriculum and re-seeds from ACADEMY_CURRICULUM."""
    is_admin = _user_get(current_user, "is_admin", False)
    if not is_admin:
        raise HTTPException(403, "Admin only")
    try:
        from .lms_init import seed_academy
        print("[RESEED] Admin triggered full reseed — clearing curriculum...", flush=True)
        await database.execute("DELETE FROM lesson_quizzes")
        await database.execute("DELETE FROM learning_lessons")
        await database.execute("DELETE FROM learning_modules")
        await database.execute("DELETE FROM learning_levels")
        print("[RESEED] Cleared. Seeding now...", flush=True)
        await seed_academy()
        r_lv = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_levels")
        r_mo = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_modules")
        r_le = await database.fetch_one("SELECT COUNT(*) AS c FROM learning_lessons")
        r_qu = await database.fetch_one("SELECT COUNT(*) AS c FROM lesson_quizzes")
        return {
            "status":  "success",
            "message": "Academy curriculum reseeded successfully",
            "levels":  r_lv["c"] if r_lv else 0,
            "modules": r_mo["c"] if r_mo else 0,
            "lessons": r_le["c"] if r_le else 0,
            "quizzes": r_qu["c"] if r_qu else 0,
        }
    except Exception as e:
        print(f"[RESEED ERROR] {e}", flush=True)
        raise HTTPException(500, f"Reseed failed: {e}")

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
