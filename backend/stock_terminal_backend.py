"""
Pipways AI Stock Research Terminal - FastAPI Backend Module
===========================================================
Mount the router into your existing FastAPI app:

    from . import stock_terminal_backend as stock_module
    app.include_router(stock_module.router, prefix="/api/stock", tags=["Stock Terminal"])

Dependencies:
    pip install fastapi anthropic yfinance python-dotenv uvicorn

Run standalone (dev):
    uvicorn stock_terminal_backend:app --port 5050 --reload

Environment variables required:
    ANTHROPIC_API_KEY   - your Anthropic key

No Alpha Vantage key needed — yfinance is free with no API key.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import yfinance as yf
from anthropic import AsyncAnthropic
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Shared async clients ──────────────────────────────────────────────────────
_anthropic: AsyncAnthropic | None = None

# ── Async-safe cache ──────────────────────────────────────────────────────────
CACHE_TTL            = 300  # seconds (5 min)
_cache_lock: asyncio.Lock | None = None
_cache:      dict[str, dict]     = {}


def _get_lock() -> asyncio.Lock:
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


# ── Lazy self-initialisation ──────────────────────────────────────────────────
def _require_anthropic() -> None:
    global _anthropic
    if _anthropic is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY is not set. Add it in Render → Environment.",
            )
        _anthropic = AsyncAnthropic(api_key=api_key)
        print("[STOCK] Anthropic client lazy-initialised", flush=True)


# ── Pydantic models ───────────────────────────────────────────────────────────

class OkResponse(BaseModel):
    ok:     bool = True
    cached: bool = False
    data:   Any


class PortfolioRequest(BaseModel):
    amount:  float = Field(default=10_000, gt=0)
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
    _require_anthropic()
    try:
        message = await _anthropic.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = max_tokens,
            system     = SYSTEM_PROMPT,
            messages   = [{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude API error: {exc}") from exc

    raw   = "".join(b.text for b in message.content if hasattr(b, "text"))
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
    if clean.endswith("```"):
        clean = clean.rsplit("```", 1)[0].strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Claude returned invalid JSON: {exc}. Raw: {raw[:300]}",
        ) from exc


# ── AI market data fallback ───────────────────────────────────────────────────

async def enrich_with_claude(symbol: str) -> dict:
    """
    When yfinance is unavailable, ask Claude to provide realistic market data
    from its training knowledge so the UI shows real values instead of all N/A.
    """
    prompt = f"""
Provide realistic and accurate market data for the stock {symbol} based on your training knowledge.
Use the most recent figures you know. Estimate conservatively if uncertain.

Return ONLY this JSON (no markdown, no explanation):
{{
  "name": "<Full company name>",
  "sector": "<sector e.g. Technology>",
  "industry": "<industry e.g. Consumer Electronics>",
  "exchange": "<e.g. NASDAQ>",
  "country": "<e.g. USA>",
  "currency": "USD",
  "price": <current approximate price as a number, e.g. 213.49>,
  "change": <typical daily change as number, e.g. 1.25>,
  "change_pct": "<e.g. 0.59>",
  "market_cap": "<formatted e.g. $3.2T or $450B>",
  "pe_ratio": "<e.g. 33.2 or N/A>",
  "forward_pe": "<e.g. 29.5 or N/A>",
  "peg_ratio": "<e.g. 2.1 or N/A>",
  "eps": "<e.g. 6.43 or N/A>",
  "beta": "<e.g. 1.24 or N/A>",
  "div_yield": "<e.g. 0.52% or N/A>",
  "52_week_high": "<e.g. 237.23 or N/A>",
  "52_week_low": "<e.g. 164.08 or N/A>",
  "50_day_avg": "<e.g. 220.5 or N/A>",
  "200_day_avg": "<e.g. 210.2 or N/A>",
  "analyst_target": "<e.g. 230.00 or N/A>",
  "profit_margin": "<e.g. 24.30% or N/A>",
  "gross_margin": "<e.g. 45.60% or N/A>",
  "operating_margin": "<e.g. 30.10% or N/A>",
  "return_on_equity": "<e.g. 160.50% or N/A>",
  "return_on_assets": "<e.g. 22.60% or N/A>",
  "revenue_ttm": "<formatted e.g. $383B or N/A>",
  "ebitda": "<formatted e.g. $130B or N/A>",
  "free_cashflow": "<formatted e.g. $90B or N/A>",
  "debt_to_equity": "<e.g. 1.87 or N/A>",
  "current_ratio": "<e.g. 0.95 or N/A>",
  "price_to_book": "<e.g. 48.5 or N/A>",
  "book_value": "<e.g. 4.38 or N/A>",
  "data_source": "ai_estimate"
}}
"""
    try:
        data = await claude_json(prompt, max_tokens=700)
        data["data_source"] = "ai_estimate"
        return data
    except Exception as exc:
        print(f"[STOCK] enrich_with_claude failed for {symbol}: {exc}", flush=True)
        return {
            "name": symbol, "sector": "N/A", "industry": "N/A",
            "exchange": "N/A", "country": "N/A", "currency": "USD",
            "price": 0, "change": 0, "change_pct": "0",
            "market_cap": "N/A", "pe_ratio": "N/A", "forward_pe": "N/A",
            "peg_ratio": "N/A", "eps": "N/A", "beta": "N/A",
            "div_yield": "N/A", "52_week_high": "N/A", "52_week_low": "N/A",
            "50_day_avg": "N/A", "200_day_avg": "N/A", "analyst_target": "N/A",
            "profit_margin": "N/A", "gross_margin": "N/A", "operating_margin": "N/A",
            "return_on_equity": "N/A", "return_on_assets": "N/A",
            "revenue_ttm": "N/A", "ebitda": "N/A", "free_cashflow": "N/A",
            "debt_to_equity": "N/A", "current_ratio": "N/A",
            "price_to_book": "N/A", "book_value": "N/A",
            "data_source": "ai_estimate",
        }


# ── yfinance market data helpers ──────────────────────────────────────────────

def _safe(val, fallback="N/A"):
    """Return a clean string value, never None/NaN/0."""
    if val is None:
        return fallback
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return fallback
    except Exception:
        pass
    if str(val).lower() in ("nan", "none", ""):
        return fallback
    return val


def _fmt_large(val) -> str:
    """Format large numbers as $1.2T / $450B / $3.2M."""
    try:
        n = float(val)
        if n >= 1e12: return f"${n/1e12:.2f}T"
        if n >= 1e9:  return f"${n/1e9:.1f}B"
        if n >= 1e6:  return f"${n/1e6:.1f}M"
        return f"${n:,.0f}"
    except Exception:
        return "N/A"


def _fmt_pct(val) -> str:
    try:
        return f"{float(val)*100:.2f}%"
    except Exception:
        return "N/A"


async def fetch_market_data(symbol: str) -> dict:
    """
    Fetch full quote + fundamentals from Yahoo Finance via yfinance.
    Runs in a thread executor so it doesn't block the async event loop.
    """
    cache_key = f"yf:{symbol}"
    if cached := await cache_get(cache_key):
        return cached

    def _fetch():
        ticker = yf.Ticker(symbol)
        info   = ticker.info or {}

        # ── Current price ──────────────────────────────────────────────────
        price      = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or 0
        change     = round(float(price) - float(prev_close), 4) if price and prev_close else 0
        change_pct = round((change / float(prev_close)) * 100, 4) if prev_close else 0

        return {
            # ── Quote ───────────────────────────────────────────────
            "symbol":        symbol,
            "price":         _safe(price, 0),
            "change":        change,
            "change_pct":    str(change_pct),
            "volume":        _safe(info.get("volume"), 0),
            "prev_close":    _safe(prev_close, 0),
            "high":          _safe(info.get("dayHigh"), 0),
            "low":           _safe(info.get("dayLow"),  0),
            # ── Company ─────────────────────────────────────────────
            "name":          _safe(info.get("longName") or info.get("shortName"), symbol),
            "sector":        _safe(info.get("sector")),
            "industry":      _safe(info.get("industry")),
            "exchange":      _safe(info.get("exchange")),
            "currency":      _safe(info.get("currency"), "USD"),
            "country":       _safe(info.get("country")),
            "description":   _safe(info.get("longBusinessSummary"), ""),
            # ── Valuation ───────────────────────────────────────────
            "market_cap":    _fmt_large(info.get("marketCap")),
            "pe_ratio":      _safe(info.get("trailingPE")),
            "forward_pe":    _safe(info.get("forwardPE")),
            "peg_ratio":     _safe(info.get("pegRatio")),
            "eps":           _safe(info.get("trailingEps")),
            "book_value":    _safe(info.get("bookValue")),
            "price_to_book": _safe(info.get("priceToBook")),
            # ── Range ───────────────────────────────────────────────
            "52_week_high":  _safe(info.get("fiftyTwoWeekHigh")),
            "52_week_low":   _safe(info.get("fiftyTwoWeekLow")),
            "50_day_avg":    _safe(info.get("fiftyDayAverage")),
            "200_day_avg":   _safe(info.get("twoHundredDayAverage")),
            # ── Dividends & Risk ────────────────────────────────────
            "div_yield":     _fmt_pct(info.get("dividendYield")) if info.get("dividendYield") else "N/A",
            "beta":          _safe(info.get("beta")),
            "analyst_target":_safe(info.get("targetMeanPrice")),
            # ── Financials ──────────────────────────────────────────
            "profit_margin":     _fmt_pct(info.get("profitMargins")),
            "gross_margin":      _fmt_pct(info.get("grossMargins")),
            "operating_margin":  _fmt_pct(info.get("operatingMargins")),
            "revenue_ttm":       _fmt_large(info.get("totalRevenue")),
            "revenue_per_share": _safe(info.get("revenuePerShare")),
            "gross_profit_ttm":  _fmt_large(info.get("grossProfits")),
            "ebitda":            _fmt_large(info.get("ebitda")),
            "free_cashflow":     _fmt_large(info.get("freeCashflow")),
            "return_on_equity":  _fmt_pct(info.get("returnOnEquity")),
            "return_on_assets":  _fmt_pct(info.get("returnOnAssets")),
            "debt_to_equity":    _safe(info.get("debtToEquity")),
            "current_ratio":     _safe(info.get("currentRatio")),
            "fiscal_year_end":   _safe(info.get("lastFiscalYearEnd")),
            # ── Meta ────────────────────────────────────────────────
            "data_source": "live",
        }

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _fetch)
        # Validate we actually got data (yfinance returns empty info for bad symbols)
        if not result.get("name") or result["name"] == symbol:
            if result.get("price", 0) == 0:
                raise ValueError(f"No data returned for '{symbol}' — check the ticker symbol.")
        await cache_set(cache_key, result)
        return result
    except ValueError:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"yfinance error for '{symbol}': {exc}") from exc


# ── Router ────────────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/quote/{symbol}", response_model=OkResponse, summary="Live market quote")
async def quote(symbol: str) -> OkResponse:
    try:
        data = await fetch_market_data(symbol.upper())
        # Return just the quote subset
        quote_keys = ["symbol", "price", "change", "change_pct", "volume", "prev_close", "high", "low"]
        return OkResponse(data={k: data[k] for k in quote_keys if k in data})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/overview/{symbol}", response_model=OkResponse, summary="Company overview")
async def overview(symbol: str) -> OkResponse:
    try:
        data = await fetch_market_data(symbol.upper())
        return OkResponse(data=data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get(
    "/analyze/{symbol}",
    response_model = OkResponse,
    summary        = "Full AI stock analysis",
    description    = "Fetches live data via yfinance then runs AI analysis. Cached 5 min.",
)
async def analyze(symbol: str) -> OkResponse:
    try:
        sym       = symbol.upper()
        cache_key = f"analysis:{sym}"

        if cached := await cache_get(cache_key):
            return OkResponse(data=cached, cached=True)

        # ── Fetch market data ─────────────────────────────────────────────
        market:      dict = {}
        data_source: str  = "live"

        try:
            market = await fetch_market_data(sym)
            print(f"[STOCK] yfinance data fetched for {sym}", flush=True)
        except Exception as exc:
            print(f"[STOCK] yfinance failed for {sym}: {exc} — falling back to AI estimates", flush=True)
            data_source = "ai_estimate"
            # Ask Claude to fill in realistic market data from its knowledge
            market = await enrich_with_claude(sym)

        # ── Build prompt ──────────────────────────────────────────────────
        data_note = (
            "NOTE: Live market data is unavailable — figures below are AI estimates from training knowledge."
            if data_source == "ai_estimate" else
            "NOTE: Live market data from Yahoo Finance."
        )

        prompt = f"""
Analyze the stock {sym} using the following live market data:
{data_note}

Company      : {market.get('name')}
Sector       : {market.get('sector')} | Industry: {market.get('industry')}
Exchange     : {market.get('exchange')} | Country: {market.get('country')}

── Price ──────────────────────────────────────────────
Current Price : ${market.get('price')}
Change Today  : {market.get('change')} ({market.get('change_pct')}%)
52w High      : {market.get('52_week_high')} | 52w Low: {market.get('52_week_low')}
50d MA        : {market.get('50_day_avg')} | 200d MA: {market.get('200_day_avg')}

── Valuation ──────────────────────────────────────────
Market Cap    : {market.get('market_cap')}
P/E (TTM)     : {market.get('pe_ratio')} | Forward P/E: {market.get('forward_pe')}
PEG Ratio     : {market.get('peg_ratio')} | Price/Book: {market.get('price_to_book')}
EPS (TTM)     : {market.get('eps')} | Book Value: {market.get('book_value')}
Analyst Target: {market.get('analyst_target')} | Beta: {market.get('beta')}
Dividend Yield: {market.get('div_yield')}

── Financials ─────────────────────────────────────────
Revenue TTM   : {market.get('revenue_ttm')} | EBITDA: {market.get('ebitda')}
Gross Margin  : {market.get('gross_margin')} | Operating Margin: {market.get('operating_margin')}
Profit Margin : {market.get('profit_margin')} | Free Cash Flow: {market.get('free_cashflow')}
ROE           : {market.get('return_on_equity')} | ROA: {market.get('return_on_assets')}
Debt/Equity   : {market.get('debt_to_equity')} | Current Ratio: {market.get('current_ratio')}

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
            "market_data": {**market, "data_source": data_source},
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
        for a in data.get("allocations", []):
            a["amount"] = round(body.amount * int(a.get("pct", 0)) / 100, 2)
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

        # Fetch all market data concurrently
        async def safe_fetch(sym: str) -> tuple[str, dict]:
            try:
                return sym, await fetch_market_data(sym)
            except Exception:
                return sym, {"name": sym, "sector": "N/A", "pe_ratio": "N/A", "beta": "N/A"}

        pairs   = await asyncio.gather(*[safe_fetch(s) for s in symbols])
        markets = dict(pairs)

        stock_context = "\n".join(
            f"- {sym}: {markets[sym].get('name', sym)}, "
            f"Sector: {markets[sym].get('sector', '?')}, "
            f"Price: ${markets[sym].get('price', '?')}, "
            f"P/E: {markets[sym].get('pe_ratio', '?')}, "
            f"Market Cap: {markets[sym].get('market_cap', '?')}, "
            f"Beta: {markets[sym].get('beta', '?')}"
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
    try:
        _require_anthropic()
    except Exception:
        pass
    return {
        "ok":              True,
        "service":         "Pipways Stock Terminal",
        "anthropic_ready": _anthropic is not None,
        "data_source":     "yfinance (free, no key needed)",
        "model":           "claude-sonnet-4-6",
    }


# ── Standalone app ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    global _anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
    _anthropic = AsyncAnthropic(api_key=api_key)
    print("✓  Pipways Stock Terminal started")
    print("   Data source  : yfinance (free)")
    print("   Model        : claude-sonnet-4-6")
    yield
    print("✓  Pipways Stock Terminal shut down")


app = FastAPI(title="Pipways AI Stock Research Terminal", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/stock", tags=["Stock Terminal"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("stock_terminal_backend:app", host="0.0.0.0", port=5050, reload=True)
