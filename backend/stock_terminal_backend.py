"""
Pipways AI Stock Research Terminal - FastAPI Backend Module
===========================================================
Mount the router into your existing FastAPI app:

    from . import stock_terminal_backend as stock_module
    app.include_router(stock_module.router, prefix="/api/stock", tags=["Stock Terminal"])

In your lifespan, initialise the shared clients:

    stock_module._anthropic = AsyncAnthropic(api_key=anthropic_key)
    stock_module._http      = httpx.AsyncClient(timeout=10.0)

And close them on shutdown:

    if stock_module._http:
        await stock_module._http.aclose()

Dependencies:
    pip install fastapi anthropic httpx python-dotenv uvicorn

Run standalone (dev):
    uvicorn stock_terminal_backend:app --port 5050 --reload

Environment variables required:
    ANTHROPIC_API_KEY   - your Anthropic key
    ALPHA_VANTAGE_KEY   - free key from alphavantage.co (25 req/day on free tier)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
from anthropic import AsyncAnthropic
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Environment ───────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "demo")
ALPHA_BASE        = "https://www.alphavantage.co/query"
CACHE_TTL         = 300  # seconds (5 min)

# ── Shared async clients ──────────────────────────────────────────────────────
# Initialised externally (via main.py lifespan) or by the standalone lifespan below.
_anthropic: AsyncAnthropic | None    = None
_http:      httpx.AsyncClient | None = None

# ── FIX 1: asyncio.Lock created lazily, NOT at module-import time.
#    Creating asyncio primitives at import time silently binds them to a
#    stale/non-existent event loop, causing "Future attached to different loop"
#    errors at runtime on some Python/uvicorn versions.
_cache_lock: asyncio.Lock | None = None
_cache:      dict[str, dict]     = {}


def _get_lock() -> asyncio.Lock:
    """Return (creating on first call) the cache lock bound to the running loop."""
    global _cache_lock
    if _cache_lock is None:
        _cache_lock = asyncio.Lock()
    return _cache_lock


async def cache_get(key: str) -> Any | None:
    async with _get_lock():
        item = _cache.get(key)
        if item and (time.monotonic() - item["ts"]) < CACHE_TTL:
            return item["data"]
    return None


async def cache_set(key: str, data: Any) -> None:
    async with _get_lock():
        _cache[key] = {"data": data, "ts": time.monotonic()}


# ── FIX 2: Guard helper raises a structured 503 JSON error if the clients
#    were never initialised (e.g. ANTHROPIC_API_KEY missing).
#    Without this, _anthropic.messages.create() throws AttributeError which
#    FastAPI serialises as plain-text "Internal Server Error", causing the
#    frontend's response.json() to fail with "Unexpected token 'I'...".
def _require_clients() -> None:
    if _anthropic is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Anthropic client not initialised. "
                "Ensure ANTHROPIC_API_KEY is set and the app lifespan has run."
            ),
        )
    if _http is None:
        raise HTTPException(
            status_code=503,
            detail="HTTP client not initialised. App lifespan may not have run.",
        )


# ── Pydantic models ───────────────────────────────────────────────────────────

class OkResponse(BaseModel):
    ok:     bool = True
    cached: bool = False
    data:   Any


class PortfolioRequest(BaseModel):
    amount:  float = Field(default=10_000, gt=0, description="Investment amount in USD")
    risk:    str   = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    horizon: str   = Field(default="long",     pattern="^(short|medium|long)$")


class CompareRequest(BaseModel):
    symbols: list[str] = Field(min_length=2, max_length=5)


# ── Claude AI helper ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an elite quantitative financial analyst and portfolio manager. "
    "You provide data-driven, objective investment analysis. "
    "Always respond with valid JSON only — no markdown, no preamble, no explanation."
)


async def claude_json(prompt: str, max_tokens: int = 1200) -> dict:
    """Call Claude asynchronously and return parsed JSON."""
    _require_clients()

    # FIX 3: Wrap the Anthropic call so any API error becomes a 502 JSON response.
    try:
        message = await _anthropic.messages.create(
            model      = "claude-opus-4-5",
            max_tokens = max_tokens,
            system     = SYSTEM_PROMPT,
            messages   = [{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc}") from exc

    raw = "".join(b.text for b in message.content if hasattr(b, "text"))

    # FIX 4: More robust markdown fence stripping.
    #    removeprefix("```json") misses "```json\n{...}\n```" because the
    #    newline is part of the prefix.  Split on the first newline instead.
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]           # drop "```json" or "```" line
    if clean.endswith("```"):
        clean = clean.rsplit("```", 1)[0].strip()  # drop trailing fence

    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Claude returned invalid JSON: {exc}. Raw (first 300 chars): {raw[:300]}",
        ) from exc


# ── Market data helpers ───────────────────────────────────────────────────────

# FIX 5: Alpha Vantage returns informational/rate-limit JSON instead of data
#    when the key is exhausted.  Detect these keys and raise a clear error.
_AV_ERROR_KEYS = {"Note", "Information", "Error Message"}


def _check_av_response(payload: dict, symbol: str) -> None:
    for key in _AV_ERROR_KEYS:
        if key in payload:
            raise HTTPException(
                status_code=429,
                detail=f"Alpha Vantage limit/error for '{symbol}': {payload[key][:200]}",
            )
    if not payload:
        raise HTTPException(
            status_code=404,
            detail=f"No data returned for '{symbol}'. Verify the ticker symbol.",
        )


async def fetch_quote(symbol: str) -> dict:
    """Async real-time quote from Alpha Vantage."""
    _require_clients()
    key = f"quote:{symbol}"
    if cached := await cache_get(key):
        return cached

    try:
        resp = await _http.get(ALPHA_BASE, params={
            "function": "GLOBAL_QUOTE",
            "symbol":   symbol,
            "apikey":   ALPHA_VANTAGE_KEY,
        })
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Market data fetch error: {exc}") from exc

    payload = resp.json()
    _check_av_response(payload, symbol)
    raw = payload.get("Global Quote", {})

    result = {
        "symbol":     symbol,
        "price":      float(raw.get("05. price",          0) or 0),
        "change":     float(raw.get("09. change",         0) or 0),
        "change_pct": raw.get("10. change percent", "0%").replace("%", "").strip(),
        "volume":     int(raw.get("06. volume",           0) or 0),
        "prev_close": float(raw.get("08. previous close", 0) or 0),
        "high":       float(raw.get("03. high",           0) or 0),
        "low":        float(raw.get("04. low",            0) or 0),
    }
    await cache_set(key, result)
    return result


async def fetch_overview(symbol: str) -> dict:
    """Async company overview / fundamentals from Alpha Vantage."""
    _require_clients()
    key = f"overview:{symbol}"
    if cached := await cache_get(key):
        return cached

    try:
        resp = await _http.get(ALPHA_BASE, params={
            "function": "OVERVIEW",
            "symbol":   symbol,
            "apikey":   ALPHA_VANTAGE_KEY,
        })
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Market data fetch error: {exc}") from exc

    d = resp.json()
    _check_av_response(d, symbol)

    result = {
        "name":              d.get("Name",                 symbol),
        "sector":            d.get("Sector",               "N/A"),
        "industry":          d.get("Industry",             "N/A"),
        "market_cap":        d.get("MarketCapitalization", "N/A"),
        "pe_ratio":          d.get("PERatio",              "N/A"),
        "eps":               d.get("EPS",                  "N/A"),
        "beta":              d.get("Beta",                 "N/A"),
        "div_yield":         d.get("DividendYield",        "N/A"),
        "52_week_high":      d.get("52WeekHigh",           "N/A"),
        "52_week_low":       d.get("52WeekLow",            "N/A"),
        "profit_margin":     d.get("ProfitMargin",         "N/A"),
        "revenue_ttm":       d.get("RevenueTTM",           "N/A"),
        "gross_profit_ttm":  d.get("GrossProfitTTM",       "N/A"),
        "ebitda":            d.get("EBITDA",               "N/A"),
        "description":       d.get("Description",          ""),
        "exchange":          d.get("Exchange",             "N/A"),
        "currency":          d.get("Currency",             "USD"),
        "country":           d.get("Country",              "N/A"),
        "fiscal_year_end":   d.get("FiscalYearEnd",        "N/A"),
        "analyst_target":    d.get("AnalystTargetPrice",   "N/A"),
        "forward_pe":        d.get("ForwardPE",            "N/A"),
        "peg_ratio":         d.get("PEGRatio",             "N/A"),
        "book_value":        d.get("BookValue",            "N/A"),
        "revenue_per_share": d.get("RevenuePerShareTTM",   "N/A"),
        "return_on_equity":  d.get("ReturnOnEquityTTM",    "N/A"),
        "return_on_assets":  d.get("ReturnOnAssetsTTM",    "N/A"),
        "debt_to_equity":    d.get("DebtToEquityRatio",    "N/A"),
        "current_ratio":     d.get("CurrentRatio",         "N/A"),
    }
    await cache_set(key, result)
    return result


# ── Router ────────────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/quote/{symbol}", response_model=OkResponse, summary="Live market quote")
async def quote(symbol: str) -> OkResponse:
    # FIX 6: All routes have a catch-all except so ANY unhandled exception
    #    returns a structured JSON 500 rather than plain-text "Internal Server Error".
    try:
        data = await fetch_quote(symbol.upper())
        return OkResponse(data=data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/overview/{symbol}", response_model=OkResponse, summary="Company overview")
async def overview(symbol: str) -> OkResponse:
    try:
        data = await fetch_overview(symbol.upper())
        return OkResponse(data=data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/analyze/{symbol}",
    response_model = OkResponse,
    summary        = "Full AI stock analysis",
    description    = "Fetches live market data then runs AI analysis. Cached for 5 min.",
)
async def analyze(symbol: str) -> OkResponse:
    try:
        sym       = symbol.upper()
        cache_key = f"analysis:{sym}"

        if cached := await cache_get(cache_key):
            return OkResponse(data=cached, cached=True)

        quote_data: dict = {"price": "N/A", "change_pct": "N/A"}
        ov:         dict = {"name": sym, "sector": "Unknown"}

        try:
            quote_data, ov = await asyncio.gather(
                fetch_quote(sym),
                fetch_overview(sym),
            )
        except HTTPException as exc:
            print(f"[STOCK] Market data degraded for {sym}: {exc.detail}", flush=True)
        except Exception as exc:
            print(f"[STOCK] Market data failed for {sym}: {exc}", flush=True)

        prompt = f"""
Analyze the stock {sym} using the following real market data:

Company: {ov.get('name')}
Sector: {ov.get('sector')} | Industry: {ov.get('industry')}
Current Price: ${quote_data.get('price')} | Change: {quote_data.get('change_pct')}%
Market Cap: {ov.get('market_cap')} | P/E: {ov.get('pe_ratio')} | Forward P/E: {ov.get('forward_pe')}
EPS: {ov.get('eps')} | PEG Ratio: {ov.get('peg_ratio')}
Beta: {ov.get('beta')} | 52w High: {ov.get('52_week_high')} | 52w Low: {ov.get('52_week_low')}
Dividend Yield: {ov.get('div_yield')} | Analyst Target: {ov.get('analyst_target')}
Profit Margin: {ov.get('profit_margin')} | ROE: {ov.get('return_on_equity')} | ROA: {ov.get('return_on_assets')}
Debt/Equity: {ov.get('debt_to_equity')} | Current Ratio: {ov.get('current_ratio')}
Revenue TTM: {ov.get('revenue_ttm')} | EBITDA: {ov.get('ebitda')}
Exchange: {ov.get('exchange')} | Country: {ov.get('country')}

Return exactly this JSON structure:
{{
  "rating": "BUY" | "HOLD" | "SELL" | "STRONG_BUY",
  "confidence": <integer 50-99>,
  "hold_period": "<e.g. Long Term (2-5 years)>",
  "scores": {{
    "Financial Strength": <0-100>,
    "Price Momentum": <0-100>,
    "Market Sentiment": <0-100>,
    "Sector Performance": <0-100>,
    "Growth Potential": <0-100>,
    "Risk Level": <0-100>
  }},
  "overall_score": <float 0.0-10.0, one decimal>,
  "weighted_score": <float 0.0-100.0>,
  "long_term_outlook": "<one clear sentence>",
  "growth_window": "<e.g. 3-7 years>",
  "risk_level": "Low" | "Medium" | "High",
  "trend": "Bullish" | "Bearish" | "Neutral",
  "momentum": "Strong" | "Moderate" | "Weak",
  "key_support": <number>,
  "key_resistance": <number>,
  "risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
  "opportunities": ["<opportunity 1>", "<opportunity 2>"],
  "summary": "<3-4 sentence human-style investment summary>",
  "short_term": "Not recommended" | "Moderate opportunity" | "Strong opportunity",
  "medium_term": "Not recommended" | "Moderate opportunity" | "Strong opportunity",
  "long_term": "Not recommended" | "Moderate opportunity" | "Strong investment candidate",
  "revenue_growth": "Weak" | "Moderate" | "Strong",
  "profit_margin_rating": "Low" | "Moderate" | "High",
  "debt_level": "Low" | "Moderate" | "High",
  "cash_flow": "Negative" | "Moderate" | "Strong",
  "competitive_moat": "Narrow" | "Wide" | "None",
  "insider_sentiment": "Bearish" | "Neutral" | "Bullish",
  "analyst_consensus": "Underperform" | "Hold" | "Buy" | "Strong Buy"
}}
"""
        ai_data = await claude_json(prompt)
        result  = {
            "symbol":      sym,
            "market_data": {**quote_data, **ov},
            "ai_analysis": ai_data,
        }
        await cache_set(cache_key, result)
        return OkResponse(data=result)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/portfolio", response_model=OkResponse, summary="AI portfolio builder")
async def portfolio(body: PortfolioRequest) -> OkResponse:
    try:
        prompt = f"""
Build an optimal diversified stock portfolio for an investor with these parameters:
- Investment amount: ${body.amount:,.2f}
- Risk tolerance: {body.risk}
- Investment horizon: {body.horizon} term

Return exactly this JSON:
{{
  "allocations": [
    {{
      "symbol": "<TICKER>",
      "name": "<Company Name>",
      "pct": <integer, all allocations must sum to exactly 100>,
      "amount": <dollar amount>,
      "rationale": "<one sentence why>",
      "asset_type": "Stock" | "ETF" | "Bond ETF"
    }}
  ],
  "expected_annual_return": "<e.g. 10-14%>",
  "expected_volatility": "Low" | "Moderate" | "High",
  "risk_profile": "<Conservative|Moderate|Aggressive>",
  "diversification_score": <0-100>,
  "summary": "<2 sentence portfolio thesis>",
  "rebalance_frequency": "Quarterly" | "Semi-Annual" | "Annual"
}}

Rules:
- 4 to 7 positions total
- Include at least 1 ETF for diversification
- Allocations must be whole numbers summing to exactly 100
- Dollar amounts must reflect the percentage of ${body.amount:,.2f}
"""
        data = await claude_json(prompt, max_tokens=1000)
        for allocation in data.get("allocations", []):
            allocation["amount"] = round(body.amount * int(allocation.get("pct", 0)) / 100, 2)
        return OkResponse(data=data)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/compare", response_model=OkResponse, summary="Side-by-side stock comparison")
async def compare(body: CompareRequest) -> OkResponse:
    try:
        symbols = [s.strip().upper() for s in body.symbols if s.strip()][:5]
        if len(symbols) < 2:
            raise HTTPException(status_code=422, detail="Provide at least 2 valid symbols")

        async def safe_overview(sym: str) -> tuple[str, dict]:
            try:
                return sym, await fetch_overview(sym)
            except Exception:
                return sym, {"name": sym}

        pairs     = await asyncio.gather(*[safe_overview(s) for s in symbols])
        overviews = dict(pairs)

        stock_context = "\n".join(
            f"- {sym}: {overviews[sym].get('name','?')}, "
            f"Sector: {overviews[sym].get('sector','?')}, "
            f"P/E: {overviews[sym].get('pe_ratio','?')}, "
            f"Beta: {overviews[sym].get('beta','?')}"
            for sym in symbols
        )

        prompt = f"""
Compare these stocks for an investor and rank them objectively:

{stock_context}

Return exactly this JSON:
{{
  "stocks": [
    {{
      "symbol": "<TICKER>",
      "rating": "BUY" | "HOLD" | "SELL",
      "overall_rank": <1 to {len(symbols)}>,
      "growth_score": <0-100>,
      "valuation_score": <0-100>,
      "risk_score": <0-100>,
      "momentum_score": <0-100>,
      "dividend_score": <0-100>,
      "one_line_summary": "<concise analyst opinion>",
      "best_for": "Growth investors" | "Income investors" | "Value investors" | "Traders"
    }}
  ],
  "winner": "<symbol>",
  "winner_reason": "<one sentence>",
  "avoid": "<symbol or null>",
  "avoid_reason": "<one sentence or null>"
}}
Provide exactly one object per symbol. Rank 1 = best overall pick.
"""
        data = await claude_json(prompt, max_tokens=900)
        return OkResponse(data=data)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Utility endpoints ─────────────────────────────────────────────────────────

@router.delete("/cache", summary="Flush the analysis cache")
async def flush_cache() -> dict:
    async with _get_lock():
        count = len(_cache)
        _cache.clear()
    return {"ok": True, "cleared": count}


@router.get("/cache/stats", summary="Cache statistics")
async def cache_stats() -> dict:
    async with _get_lock():
        total   = len(_cache)
        now     = time.monotonic()
        live    = sum(1 for v in _cache.values() if (now - v["ts"]) < CACHE_TTL)
        expired = total - live
    return {"ok": True, "total": total, "live": live, "expired": expired, "ttl_seconds": CACHE_TTL}


@router.get("/health", include_in_schema=False)
async def health() -> dict:
    return {
        "ok":              True,
        "service":         "Pipways Stock Terminal",
        "anthropic_ready": _anthropic is not None,
        "http_ready":      _http is not None,
        "alpha_vantage":   "demo (25 req/day)" if ALPHA_VANTAGE_KEY == "demo" else "configured",
    }


# ── Standalone app (dev only — not used when imported by main.py) ─────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    global _anthropic, _http
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
    _anthropic = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    _http      = httpx.AsyncClient(timeout=10.0)
    print("✓  Pipways Stock Terminal started (standalone)")
    print(f"   Alpha Vantage: {'custom' if ALPHA_VANTAGE_KEY != 'demo' else 'demo (25 req/day limit)'}")
    yield
    await _http.aclose()
    print("✓  Pipways Stock Terminal shut down")


app = FastAPI(title="Pipways AI Stock Research Terminal", version="2.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/stock", tags=["Stock Terminal"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("stock_terminal_backend:app", host="0.0.0.0", port=5050, reload=True)
