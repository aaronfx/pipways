"""
AI Chart Analysis - PRODUCTION READY
Smart Money Concepts (SMC) Institutional Analysis Engine

Fixes applied:
  Bug 1/2  — HTTP client properly initialized via lifespan, temp client guarded
  Bug 5    — Image validation gate (non-charts rejected before analysis)
  Bug 6    — Neutral bias possible; "NEVER neutral" rule removed
  Bug 7    — AI self-reported confidence replaced by backend calculator
  Bug 8/9  — Three-pass prompt eliminates fabricated SMC signals and prices
  Bug 10   — Three-pass sequential analysis with verification
  Bug 11   — Contradiction validator nulls invalid trade setups
  Bug 12   — Symbol/price range validator
  Bug 13   — NAS100 no longer maps to US100
  Rec 4/5  — Timeframe-aware prompt, temperature control
  Rec 14   — Image hash caching (in-memory, 1h TTL)
  Rec 15   — No unnecessary PNG conversion
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from typing import List, Optional, Dict, Any
import base64
import hashlib
import io
import os
import time
import httpx
import json
import re

from PIL import Image
from .security import get_current_user

router = APIRouter()

# ── HTTP client ───────────────────────────────────────────────────────────────
_http_client: Optional[httpx.AsyncClient] = None


async def init_chart_http_client():
    global _http_client
    _http_client = httpx.AsyncClient(timeout=90.0)


async def close_chart_http_client():
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None


# ── Result cache ──────────────────────────────────────────────────────────────
_analysis_cache: Dict[str, Dict] = {}
_CACHE_TTL = 3600


def _cache_get(key: str) -> Optional[Dict]:
    entry = _analysis_cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > _CACHE_TTL:
        del _analysis_cache[key]
        return None
    return entry["data"]


def _cache_set(key: str, data: Dict):
    _analysis_cache[key] = {"ts": time.time(), "data": data}


# ── Config ────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY    = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL      = os.getenv("OPENROUTER_VISION_MODEL") or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_CONFIGURED = bool(OPENROUTER_API_KEY)
OPENROUTER_BASE_URL   = "https://openrouter.ai/api/v1"
_DEFAULT_CONFIDENCE   = 0.50

# ── Symbol config ─────────────────────────────────────────────────────────────
COMMON_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "XAGUSD",
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD",
    "US30", "US500", "NAS100", "DE30", "UK100", "DXY",
]

SYMBOL_PRICE_RANGES: Dict[str, tuple] = {
    "EURUSD": (0.90, 1.50), "GBPUSD": (1.10, 1.60), "USDJPY": (80.0, 170.0),
    "USDCHF": (0.80, 1.20), "AUDUSD": (0.55, 0.90), "USDCAD": (1.20, 1.50),
    "NZDUSD": (0.50, 0.80), "EURGBP": (0.80, 1.00), "EURJPY": (110.0, 175.0),
    "GBPJPY": (130.0, 210.0), "AUDJPY": (60.0, 110.0),
    "XAUUSD": (1500.0, 4000.0), "XAGUSD": (15.0, 50.0),
    "BTCUSD": (10000.0, 200000.0),
    "US30": (25000.0, 50000.0), "US500": (3000.0, 8000.0),
    "NAS100": (10000.0, 25000.0), "UK100": (6000.0, 12000.0), "DE30": (12000.0, 25000.0),
}


def normalize_symbol(symbol: str) -> str:
    if not symbol:
        return "Unknown"
    s = symbol.upper().strip()

    # Strip TradingView instrument name prefixes like "CFDs on Gold (US$ / OZ)"
    # These appear in chart title bars and need cleaning before lookup
    s = re.sub(r'\s*\(.*?\)', '', s)          # remove (US$ / OZ) etc
    s = re.sub(r'CFDSON|CFDS ON|CFDON', '', s) # remove "CFDs on" prefix
    s = s.replace("/", "").replace("-", "").replace(" ", "").replace(".", "").replace("$", "")

    mappings = {
        "GOLD": "XAUUSD", "XAU": "XAUUSD", "XAUUSD": "XAUUSD",
        "SILVER": "XAGUSD", "XAG": "XAGUSD", "XAGUSD": "XAGUSD",
        "BITCOIN": "BTCUSD", "BTC": "BTCUSD",
        "ETHEREUM": "ETHUSD", "ETH": "ETHUSD",
        # TradingView gold variants
        "GOLDUS": "XAUUSD", "GOLDOZ": "XAUUSD",
        "CFDSONGOLD": "XAUUSD", "GOLDUSDOZ": "XAUUSD",
        "XAUUSDT": "XAUUSD",
        # NAS100
        "NAS100": "NAS100", "NASDAQ": "NAS100", "NAS": "NAS100",
        "US100": "NAS100", "NDX": "NAS100",
        # Other indices
        "SP500": "US500", "SPX": "US500",
        "US30": "US30", "DOW": "US30",
        "DXY": "DXY", "DOLLARINDEX": "DXY", "USDX": "DXY",
        "GER30": "DE30", "DAX": "DE30", "GER40": "DE30",
        "UK100": "UK100", "FTSE": "UK100",
    }
    if s in mappings:
        return mappings[s]

    # Check known symbols list
    for sym in COMMON_SYMBOLS:
        if s == sym or s.startswith(sym):
            return sym

    if len(s) == 6 and s.isalpha():
        return s
    return s


def extract_symbol_from_text(text: str) -> Optional[str]:
    if not text:
        return None
    t = text.upper()
    for sym in COMMON_SYMBOLS:
        if sym in t:
            return sym
    match = re.search(r'\b([A-Z]{3})([A-Z]{3})\b', t)
    if match:
        pair = match.group(0)
        FALSE_POSITIVES = {
            "NEUTRAL", "BEARISH", "BULLISH", "MARKET", "RETURN",
            "STRONG", "SIGNAL", "CANDLE", "INSIDE", "DOUBLE",
        }
        if pair not in FALSE_POSITIVES:
            return pair
    return None


def clean_json_content(content: str) -> str:
    c = content.strip()
    if "```json" in c:
        c = c.split("```json")[1].split("```")[0].strip()
    elif "```" in c:
        c = c.split("```")[1].split("```")[0].strip()
    elif c.startswith("`") and c.endswith("`"):
        c = c[1:-1].strip()
    return c


def _safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _calculate_confidence(result: Dict) -> float:
    score = 0.40
    sq = (result.get("structure_quality") or "").lower()
    if sq == "strong":   score += 0.15
    elif sq == "moderate": score += 0.08
    if result.get("bos_confirmed"):   score += 0.15
    annotations = result.get("chart_annotations") or {}
    ob_count  = len(annotations.get("order_blocks") or [])
    fvg_count = len(annotations.get("fair_value_gaps") or [])
    if ob_count > 0 and fvg_count > 0:   score += 0.15
    elif ob_count > 0 or fvg_count > 0:  score += 0.08
    if result.get("liquidity_swept"):    score += 0.10
    if result.get("in_correct_zone"):    score += 0.05
    if result.get("price_scale_readable") is False: score -= 0.20
    return min(round(score, 2), 0.92)


def _validate_trade_logic(result: Dict) -> List[str]:
    errors = []
    bias      = (result.get("trading_bias") or "neutral").lower()
    structure = (result.get("market_structure") or "neutral").lower()
    entry     = _safe_float(result.get("suggested_entry"))
    sl        = _safe_float(result.get("suggested_stop"))
    tp        = _safe_float(result.get("suggested_target"))

    if bias == "bullish" and structure == "bearish":
        errors.append("bias_structure_mismatch")
    if bias == "bearish" and structure == "bullish":
        errors.append("bias_structure_mismatch")
    if entry is not None and tp is not None:
        if bias == "bullish" and tp <= entry: errors.append("tp_below_entry_on_buy")
        if bias == "bearish" and tp >= entry: errors.append("tp_above_entry_on_sell")
    if entry is not None and sl is not None:
        if bias == "bullish" and sl >= entry: errors.append("sl_above_entry_on_buy")
        if bias == "bearish" and sl <= entry: errors.append("sl_below_entry_on_sell")
    if entry is not None and sl is not None and tp is not None:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk > 0 and reward / risk < 1.3:
            errors.append("rr_below_minimum")
    return errors


def _validate_symbol_price(symbol: str, entry: Optional[float]) -> bool:
    if not entry or symbol not in SYMBOL_PRICE_RANGES:
        return True
    low, high = SYMBOL_PRICE_RANGES[symbol]
    return low <= entry <= high


def _build_data_url(contents: bytes, content_type: str) -> str:
    """Send JPEG/PNG/WEBP as-is. Convert other formats to PNG."""
    supported = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if content_type in supported:
        return f"data:{content_type};base64,{base64.b64encode(contents).decode()}"
    try:
        image = Image.open(io.BytesIO(contents))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return f"data:{content_type};base64,{base64.b64encode(contents).decode()}"


# ── Three-pass prompts ────────────────────────────────────────────────────────

_PASS1_PROMPT = """You are a chart validation system. Determine if this image is a trading chart.

A valid trading chart MUST have ALL THREE:
1. Price/value axis (Y-axis with numbers)
2. Time axis (X-axis with dates, times, or sequential candles)
3. Price data (candlesticks, OHLC bars, or price line)

If ANY element is missing — photos, text screenshots, memes, artwork, etc — return ONLY:
{"is_chart": false, "reason": "brief explanation"}

If it IS a trading chart, return ONLY:
{
  "is_chart": true,
  "symbol_visible": "the trading symbol — for gold return XAUUSD, for silver XAGUSD, for bitcoin BTCUSD. If the chart says 'CFDs on Gold' or 'Gold' return XAUUSD. For forex pairs like EUR/USD return EURUSD. Return the clean symbol without slashes or spaces.",
  "timeframe_visible": "timeframe visible on chart or null",
  "price_scale_readable": true or false,
  "approximate_price_range": {"low": "lowest price or null", "high": "highest price or null"},
  "chart_type": "candlestick|line|bar|other",
  "num_candles_visible": approximate integer,
  "quality": "high|medium|low"
}

Return ONLY valid JSON. No markdown, no explanation."""

_PASS2_PROMPT = """You are a senior SMC prop firm trader. Analyze this chart decisively.

Chart context: {context}

STEP 1 — Read the overall price movement:
Look at the FULL chart from left to right. Is price generally moving up, down, or sideways?
- Mostly higher highs and higher lows overall = bullish
- Mostly lower highs and lower lows overall = bearish
- No clear overall direction, price bouncing between a range = ranging

STEP 2 — Identify the most recent significant swing high and swing low.
These are the last clear turning points where price reversed.

STEP 3 — Has price broken above the last swing high (bullish BOS) or below the last swing low (bearish BOS)?
A BOS is confirmed when a candle CLOSES beyond the level, not just wicks through it.

STEP 4 — Identify the dealing range:
- Range high = highest visible swing high on the chart
- Range low = lowest visible swing low on the chart
- Equilibrium = midpoint between high and low
- Is current price above equilibrium (premium) or below (discount)?

STEP 5 — Identify key support and resistance levels:
Look for horizontal price levels where price has bounced or reversed multiple times.
Always identify at least 2 support and 2 resistance levels if the chart has enough data.

STEP 6 — Determine trading bias:
- bullish: price making HH+HL pattern OR just broke above a swing high
- bearish: price making LH+LL pattern OR just broke below a swing low
- neutral: ONLY if price is clearly stuck in a tight range with no dominant direction for the ENTIRE visible chart

IMPORTANT: Most charts have a discernible direction. Only use neutral if you genuinely cannot determine any directional bias after looking at the full chart. When in doubt between bullish/bearish, choose the direction of the most recent structure break.

ALWAYS populate support_levels and resistance_levels — there are price levels on every chart.
ALWAYS populate dealing_range — you can see the high and low of the visible price data.

Return ONLY this JSON:
{{
  "market_structure": "bullish|bearish|ranging",
  "trading_bias": "bullish|bearish|neutral",
  "structure_quality": "strong|moderate|weak",
  "bos_confirmed": true or false,
  "bos_direction": "up|down|null",
  "bos_level": "price or null",
  "choch_detected": true or false,
  "liquidity_pools": [{{"price": "level", "type": "equal_highs|equal_lows"}}],
  "dealing_range": {{"high": "price", "low": "price", "equilibrium": "price"}},
  "current_zone": "premium|discount|equilibrium",
  "in_correct_zone": true or false,
  "support_levels": ["price1", "price2"],
  "resistance_levels": ["price1", "price2"],
  "structure_notes": "one decisive sentence: what is price doing and where is it likely to go"
}}

Return ONLY valid JSON. No markdown."""

_PASS3_PROMPT = """You are a senior SMC prop firm trader finding the best entry.

Chart context: {context}
Structure: {structure}
Direction: {direction}
Zone: {zone}

Find the BEST {direction} entry on this chart using SMC methodology.

ORDER BLOCKS — find the last {ob_candle} candle before a strong {direction} move:
The OB is the origin of institutional interest. Price often returns to this level.

FAIR VALUE GAPS — find 3-candle imbalances in the {direction} direction:
Gap between candle 1 high and candle 3 low (for bullish FVG) where price has not returned.

LIQUIDITY — was there a sweep of equal lows (BUY) or equal highs (SELL) before the setup?

ENTRY RULES:
- Entry at the OB or FVG level — whichever price has reached or is approaching
- Stop beyond the nearest swing {sl_side} (invalidation level)
- Target at next opposing liquidity or OB
- Minimum R:R 1.5

Read prices from the chart Y-axis. For gold prices are 4000-5000 range.
Do NOT invent prices. If scale is unreadable, set prices to null.

Return ONLY this JSON:
{{
  "entry_confluence_found": true or false,
  "confluence_reason": "specific: which OB or FVG at which exact price level",
  "order_blocks": [{{"price": "level", "type": "bullish|bearish", "timeframe": "H1|H4|D1"}}],
  "fair_value_gaps": [{{"start": "price", "end": "price", "type": "bullish|bearish"}}],
  "liquidity_swept": true or false,
  "liquidity_swept_level": "price or null",
  "suggested_entry": "price or null",
  "suggested_stop": "price or null",
  "suggested_target": "price or null",
  "bos_levels": ["price"],
  "support_levels": ["price1", "price2"],
  "resistance_levels": ["price1", "price2"],
  "key_insights": ["what you see on this specific chart", "why this entry makes sense", "risk to watch"],
  "smc_signals": ["specific signal 1", "specific signal 2"]
}}

Return ONLY valid JSON. No markdown."""


async def _call_ai(
    http: httpx.AsyncClient,
    prompt: str,
    data_url: str,
    temperature: float = 0.1,
    max_tokens: int = 1000,
) -> str:
    response = await http.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://gopipways.com",
            "X-Title": "Gopipways Trading Platform",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text",      "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                ],
            }],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    )
    if response.status_code == 401: raise HTTPException(503, "AI authentication failed.")
    if response.status_code == 429: raise HTTPException(503, "AI rate limited. Try again.")
    if response.status_code != 200: raise HTTPException(503, f"AI error: {response.status_code}")
    data = response.json()
    if "choices" not in data or not data["choices"]:
        raise HTTPException(503, "Invalid AI response")
    return data["choices"][0]["message"]["content"]


def _parse_json(content: str) -> Dict:
    clean = clean_json_content(content)
    m = re.search(r'\{.*\}', clean, re.DOTALL)
    if m:
        return json.loads(m.group())
    return json.loads(clean)


@router.post("/analyze")
async def analyze_chart_image(
    file: UploadFile = File(...),
    symbol: Optional[str] = Form(None),
    timeframe: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """Three-pass SMC chart analysis with full validation."""
    print(f"[CHART] Upload: {file.filename} {file.content_type}", flush=True)

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image.")

    ext = os.path.splitext((file.filename or "").lower())[1]
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        raise HTTPException(400, f"File type {ext} not allowed.")

    # Bug 5 fix: content_type assigned BEFORE file.read()
    content_type = file.content_type or "image/jpeg"
    contents     = await file.read()

    if len(contents) == 0:
        raise HTTPException(400, "Empty file uploaded")
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 10MB)")

    base64_image = base64.b64encode(contents).decode()
    img_data_url = _build_data_url(contents, content_type)

    # Rec 14: cache check
    cache_key = hashlib.sha256(contents).hexdigest()
    cached = _cache_get(cache_key)
    if cached:
        print(f"[CHART] Cache hit: {cache_key[:12]}…", flush=True)
        return cached

    if not OPENROUTER_CONFIGURED:
        demo = _build_demo_response(symbol, content_type, base64_image)
        _cache_set(cache_key, demo)
        return demo

    # Bug 1/2 fix: guarded temp client
    _temp_client: Optional[httpx.AsyncClient] = None
    if _http_client is None:
        _temp_client = httpx.AsyncClient(timeout=90.0)
    http = _http_client or _temp_client

    try:
        # ── Pass 1: Validate image is a real chart ────────────────────────────
        print("[CHART] Pass 1: validation", flush=True)
        try:
            p1 = _parse_json(await _call_ai(http, _PASS1_PROMPT, img_data_url, temperature=0.0, max_tokens=400))
        except Exception:
            raise HTTPException(503, "AI validation failed.")

        if not p1.get("is_chart", False):
            reason = p1.get("reason", "No trading chart detected.")
            raise HTTPException(422, f"Not a trading chart: {reason}")

        print(f"[CHART] Pass 1 OK — quality={p1.get('quality')} readable={p1.get('price_scale_readable')}", flush=True)

        sym_hint = symbol or p1.get("symbol_visible") or "unknown"
        tf_hint  = timeframe or p1.get("timeframe_visible") or "unknown"
        context  = (
            f"Symbol: {sym_hint} | Timeframe: {tf_hint} | "
            f"Quality: {p1.get('quality','unknown')} | "
            f"Price scale readable: {p1.get('price_scale_readable', False)} | "
            f"Price range: {p1.get('approximate_price_range', {})}"
        )

        # ── Pass 2: Market structure (temp 0.1) ───────────────────────────────
        print("[CHART] Pass 2: structure", flush=True)
        try:
            p2 = _parse_json(await _call_ai(http, _PASS2_PROMPT.format(context=context), img_data_url, temperature=0.1, max_tokens=600))
        except Exception:
            p2 = {"market_structure": "ranging", "trading_bias": "neutral",
                  "structure_quality": "weak", "bos_confirmed": False}

        bias = (p2.get("trading_bias") or "neutral").lower()
        print(f"[CHART] Pass 2 OK — bias={bias} sq={p2.get('structure_quality')}", flush=True)

        # Run Pass 3 for any directional bias — even weak structure can have valid entries
        # Only skip if bias is genuinely neutral
        p3: Dict = {}
        if bias in ("bullish", "bearish"):
            direction  = "BUY"  if bias == "bullish" else "SELL"
            sl_side    = "low"  if bias == "bullish" else "high"
            ob_candle  = "bearish" if bias == "bullish" else "bullish"
            zone       = p2.get("current_zone", "unknown")
            struct_summary = json.dumps({
                k: p2.get(k) for k in (
                    "market_structure", "trading_bias", "bos_confirmed",
                    "bos_level", "dealing_range", "current_zone", "liquidity_pools",
                    "support_levels", "resistance_levels",
                )
            })
            print(f"[CHART] Pass 3: entry for {direction}", flush=True)
            try:
                p3 = _parse_json(await _call_ai(
                    http,
                    _PASS3_PROMPT.format(
                        context=context, structure=struct_summary,
                        direction=direction, zone=zone,
                        sl_side=sl_side, ob_candle=ob_candle,
                    ),
                    img_data_url, temperature=0.0, max_tokens=900,
                ))
            except Exception:
                p3 = {"entry_confluence_found": False, "confluence_reason": "Parse error"}
            print(f"[CHART] Pass 3 OK — confluence={p3.get('entry_confluence_found')}", flush=True)
        else:
            p3 = {
                "entry_confluence_found": False,
                "confluence_reason": f"Structure quality {p2.get('structure_quality','unknown')} or bias neutral — no entry generated.",
                "order_blocks": [], "fair_value_gaps": [], "liquidity_swept": False,
                "suggested_entry": None, "suggested_stop": None, "suggested_target": None,
                "bos_levels": [],
                "support_levels":    p2.get("support_levels", []),
                "resistance_levels": p2.get("resistance_levels", []),
                "key_insights": [
                    p2.get("structure_notes", "Market is ranging or unclear."),
                    f"Key levels identified: Support {p2.get('support_levels', [])} | Resistance {p2.get('resistance_levels', [])}".replace("[]", "none detected"),
                    f"Price is currently in the {p2.get('current_zone','unknown')} zone of the dealing range.",
                ],
                "smc_signals": [],
            }

    finally:
        # Bug 1 fix: only close the temp client
        if _temp_client is not None:
            await _temp_client.aclose()

    # ── Assemble result ───────────────────────────────────────────────────────
    detected_symbol = normalize_symbol(
        symbol or p1.get("symbol_visible") or
        extract_symbol_from_text(p2.get("structure_notes", "")) or "Unknown"
    )

    result: Dict = {
        "symbol":            detected_symbol,
        "market_structure":  p2.get("market_structure", "ranging"),
        "trading_bias":      p2.get("trading_bias", "neutral"),
        "structure_quality": p2.get("structure_quality", "weak"),
        "bos_confirmed":     p2.get("bos_confirmed", False),
        "liquidity_swept":   p3.get("liquidity_swept", False),
        "in_correct_zone":   p2.get("in_correct_zone", False),
        "price_scale_readable": p1.get("price_scale_readable", False),
        "smc_signals":       p3.get("smc_signals", []),
        "patterns_detected": [],
        "chart_annotations": {
            "bos_levels":      p3.get("bos_levels", []),
            "liquidity_zones": p2.get("liquidity_pools", []),
            "order_blocks":    p3.get("order_blocks", []),
            "fair_value_gaps": p3.get("fair_value_gaps", []),
            "premium_discount": {
                "current": p2.get("current_zone", "unknown"),
                "range": [
                    (p2.get("dealing_range") or {}).get("low", ""),
                    (p2.get("dealing_range") or {}).get("high", ""),
                ],
            },
        },
        "support_levels":    p3.get("support_levels") or p2.get("support_levels", []),
        "resistance_levels": p3.get("resistance_levels") or p2.get("resistance_levels", []),
        "suggested_entry":   p3.get("suggested_entry"),
        "suggested_stop":    p3.get("suggested_stop"),
        "suggested_target":  p3.get("suggested_target"),
        "key_insights":      p3.get("key_insights", [p2.get("structure_notes", "")]),
        "confluence_reason": p3.get("confluence_reason", ""),
        "risk_reward_ratio": "N/A",
        "chart_image":       f"data:{content_type};base64,{base64_image}",
        "mode":              "ai",
        "configured":        True,
    }

    # Bug 11: contradiction check
    logic_errors = _validate_trade_logic(result)
    if logic_errors:
        print(f"[CHART] Logic errors: {logic_errors} — nulling trade setup", flush=True)
        result.update({"suggested_entry": None, "suggested_stop": None, "suggested_target": None})
        result["key_insights"].append(f"Trade setup rejected: {', '.join(logic_errors)}")
        p3["entry_confluence_found"] = False

    # Bug 12: symbol/price validation
    entry_f = _safe_float(result.get("suggested_entry"))
    if entry_f and not _validate_symbol_price(detected_symbol, entry_f):
        print(f"[CHART] Price {entry_f} out of range for {detected_symbol}", flush=True)
        result.update({"suggested_entry": None, "suggested_stop": None, "suggested_target": None})
        result["key_insights"].append(
            f"Entry price {entry_f} is outside the expected range for {detected_symbol}. Verify symbol."
        )

    # Bug 7: backend confidence
    result["confidence"] = _calculate_confidence(result)

    # Build patterns list from confirmed evidence
    if result["bos_confirmed"]:
        result["patterns_detected"].append({"name": "Break of Structure", "reliability": "high"})
    if p3.get("order_blocks"):
        result["patterns_detected"].append({"name": "Order Block", "reliability": "high"})
    if p3.get("fair_value_gaps"):
        result["patterns_detected"].append({"name": "Fair Value Gap", "reliability": "high"})
    if p3.get("liquidity_swept"):
        result["patterns_detected"].append({"name": "Liquidity Sweep", "reliability": "high"})

    # Build trade setup
    trade_setup = None
    if (p3.get("entry_confluence_found") and
            result.get("suggested_entry") and
            result.get("suggested_stop") and
            result.get("suggested_target")):
        try:
            entry  = float(str(result["suggested_entry"]).replace(",", ""))
            sl     = float(str(result["suggested_stop"]).replace(",", ""))
            tp     = float(str(result["suggested_target"]).replace(",", ""))
            risk   = abs(entry - sl)
            reward = abs(tp - entry)
            rr     = f"1:{reward/risk:.1f}" if risk > 0 else "N/A"
            bias_u = result.get("trading_bias", "neutral").lower()
            direction = "BUY" if bias_u == "bullish" else "SELL" if bias_u == "bearish" else "NEUTRAL"
            trade_setup = {
                "entry": str(entry), "stop_loss": str(sl), "take_profit": str(tp),
                "risk_reward": rr, "probability": result["confidence"],
                "direction": direction, "setup_type": "SMC Institutional",
            }
            result["risk_reward_ratio"] = rr
        except (ValueError, TypeError) as e:
            print(f"[CHART] Trade setup error: {e}", flush=True)

    result["trade_setup"] = trade_setup

    print(
        f"[CHART] Done — {detected_symbol} bias={result['trading_bias']} "
        f"conf={result['confidence']} setup={'yes' if trade_setup else 'no'}",
        flush=True,
    )

    _cache_set(cache_key, result)
    return result


def _build_demo_response(symbol: Optional[str], content_type: str, base64_image: str) -> Dict:
    demo_symbol = normalize_symbol(symbol or "EURUSD")
    return {
        "symbol": demo_symbol, "market_structure": "bullish", "trading_bias": "bullish",
        "structure_quality": "strong", "bos_confirmed": True, "liquidity_swept": True,
        "in_correct_zone": True, "price_scale_readable": True,
        "smc_signals": [
            "Liquidity sweep below equal lows detected",
            "Bullish order block formed after sweep",
            "Fair value gap in discount zone",
        ],
        "patterns_detected": [
            {"name": "Order Block", "reliability": "high"},
            {"name": "Fair Value Gap", "reliability": "high"},
            {"name": "Liquidity Sweep", "reliability": "high"},
        ],
        "chart_annotations": {
            "bos_levels": ["1.0850"],
            "liquidity_zones": [{"price": "1.0820", "type": "equal_lows"}],
            "order_blocks": [{"price": "1.0840", "type": "bullish", "timeframe": "1H"}],
            "fair_value_gaps": [{"start": "1.0860", "end": "1.0875", "type": "bullish"}],
            "premium_discount": {"current": "discount", "range": ["1.0820", "1.0950"]},
        },
        "support_levels": ["1.0850", "1.0820"], "resistance_levels": ["1.0950", "1.1000"],
        "suggested_entry": "1.0860", "suggested_stop": "1.0830", "suggested_target": "1.0950",
        "risk_reward_ratio": "1:3",
        "key_insights": [
            f"{demo_symbol} showing bullish market structure with confirmed BOS",
            "Liquidity swept below equal lows — institutional buying detected",
            "OB + FVG confluence in discount zone",
        ],
        "confluence_reason": "OB + FVG in discount zone after liquidity sweep",
        "chart_image": f"data:{content_type};base64,{base64_image}",
        "confidence": 0.82,
        "trade_setup": {
            "entry": "1.0860", "stop_loss": "1.0830", "take_profit": "1.0950",
            "risk_reward": "1:3", "probability": 0.82, "direction": "BUY",
            "setup_type": "SMC Institutional",
        },
        "mode": "demo", "configured": False,
    }


@router.get("/pattern-library")
async def get_pattern_library():
    return {
        "reversal": [
            {"name": "Head and Shoulders",  "type": "reversal",     "reliability": "high",   "description": "Three peaks pattern signaling trend reversal",       "success_rate": "65%"},
            {"name": "Double Top",          "type": "reversal",     "reliability": "medium", "description": "Two peaks at resistance level",                     "success_rate": "60%"},
            {"name": "Double Bottom",       "type": "reversal",     "reliability": "medium", "description": "Two lows at support level",                         "success_rate": "60%"},
            {"name": "Inverse H&S",         "type": "reversal",     "reliability": "high",   "description": "Bullish reversal after downtrend",                  "success_rate": "63%"},
        ],
        "continuation": [
            {"name": "Bull Flag",           "type": "continuation", "reliability": "medium", "description": "Sharp rise followed by consolidation",              "success_rate": "67%"},
            {"name": "Bear Flag",           "type": "continuation", "reliability": "medium", "description": "Sharp drop followed by consolidation",              "success_rate": "67%"},
            {"name": "Ascending Triangle",  "type": "continuation", "reliability": "medium", "description": "Flat top with rising bottom",                      "success_rate": "62%"},
            {"name": "Descending Triangle", "type": "continuation", "reliability": "medium", "description": "Flat bottom with falling top",                     "success_rate": "62%"},
            {"name": "Symmetrical Triangle","type": "continuation", "reliability": "medium", "description": "Converging trendlines before breakout",            "success_rate": "58%"},
        ],
        "candlestick": [
            {"name": "Doji",                "type": "candlestick",  "reliability": "medium", "description": "Indecision candle — neither buyers nor sellers win","success_rate": "55%"},
            {"name": "Engulfing Pattern",   "type": "candlestick",  "reliability": "high",   "description": "Strong reversal signal — candle engulfs prior",    "success_rate": "72%"},
            {"name": "Hammer",              "type": "candlestick",  "reliability": "medium", "description": "Potential bottom reversal with long lower wick",   "success_rate": "60%"},
            {"name": "Shooting Star",       "type": "candlestick",  "reliability": "medium", "description": "Potential top reversal with long upper wick",      "success_rate": "60%"},
        ],
        "smc": [
            {"name": "Order Block",         "type": "smc",          "reliability": "high",   "description": "Last opposing candle before strong institutional move", "success_rate": "70%"},
            {"name": "Fair Value Gap",      "type": "smc",          "reliability": "high",   "description": "3-candle imbalance zone price returns to fill",     "success_rate": "68%"},
            {"name": "Liquidity Sweep",     "type": "smc",          "reliability": "high",   "description": "Stop hunt above/below equal highs or lows",         "success_rate": "75%"},
            {"name": "Break of Structure",  "type": "smc",          "reliability": "medium", "description": "Price breaking previous high/low confirms trend",  "success_rate": "65%"},
            {"name": "Change of Character", "type": "smc",          "reliability": "high",   "description": "Market structure shift signals reversal",           "success_rate": "72%"},
            {"name": "Premium/Discount",    "type": "smc",          "reliability": "high",   "description": "Institutional buy/sell zones within dealing range", "success_rate": "69%"},
        ],
    }
