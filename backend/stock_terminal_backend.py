"""
Pipways AI Stock Research Terminal - FastAPI Backend Module
===========================================================
Mount the router into your existing FastAPI app:

    from . import stock_terminal_backend as stock_module
    app.include_router(stock_module.router, prefix="/api/stock", tags=["Stock Terminal"])

Dependencies:
    pip install fastapi anthropic httpx python-dotenv uvicorn

Environment variables required:
    ANTHROPIC_API_KEY   - your Anthropic key (console.anthropic.com)
    EODHD_API_KEY       - your EODHD key (eodhd.com) — free tier: 20 req/day

EODHD endpoints used:
    /real-time/{symbol}.{exchange}    → live quote
    /fundamentals/{symbol}.{exchange} → full fundamentals
    Both require ?api_token=YOUR_KEY&fmt=json
"""

from __future__ import annotations

import asyncio
import json
import math
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
EODHD_API_KEY     = os.environ.get("EODHD_API_KEY", "")
EODHD_BASE        = "https://eodhd.com/api"
CACHE_TTL         = 300  # 5 minutes

# ── Shared clients ────────────────────────────────────────────────────────────
_anthropic: AsyncAnthropic | None    = None
_http:      httpx.AsyncClient | None = None

# ── Async-safe cache ──────────────────────────────────────────────────────────
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
def _require_clients() -> None:
    global _anthropic, _http

    if _anthropic is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY is not set. Add it in Render → Environment.",
            )
        _anthropic = AsyncAnthropic(api_key=api_key)
        print("[STOCK] Anthropic client lazy-initialised", flush=True)

    if _http is None:
        _http = httpx.AsyncClient(timeout=15.0)
        print("[STOCK] HTTP client lazy-initialised", flush=True)


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


class NgxAnalyzeRequest(BaseModel):
    ticker:        str = Field(min_length=1, max_length=20)
    analysis_type: str = Field(default="full", pattern="^(fundamental|technical|full)$")


class NgxPicksRequest(BaseModel):
    sector:        str = Field(default="all sectors")
    signal_filter: str = Field(default="BUY", pattern="^(BUY|all)$")


# ── Claude AI helper ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are an elite quantitative financial analyst and portfolio manager. "
    "You provide data-driven, objective investment analysis. "
    "Always respond with valid JSON only — no markdown, no preamble, no explanation."
)


async def claude_json(prompt: str, max_tokens: int = 1200) -> dict:
    _require_clients()
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


# ── EODHD helpers ─────────────────────────────────────────────────────────────

def _safe(val: Any, fallback: str = "N/A") -> Any:
    """Return value or fallback if None / NaN / empty."""
    if val is None:
        return fallback
    try:
        if isinstance(val, float) and math.isnan(val):
            return fallback
    except Exception:
        pass
    if str(val).strip().lower() in ("nan", "none", "", "null", "0"):
        return fallback
    return val


def _fmt_large(val: Any) -> str:
    """Format large numbers → $1.2T / $450B / $3.2M."""
    try:
        n = float(val)
        if n == 0:
            return "N/A"
        if n >= 1e12: return f"${n/1e12:.2f}T"
        if n >= 1e9:  return f"${n/1e9:.1f}B"
        if n >= 1e6:  return f"${n/1e6:.1f}M"
        return f"${n:,.0f}"
    except Exception:
        return "N/A"


def _fmt_pct(val: Any) -> str:
    """Format ratio → percentage string."""
    try:
        f = float(val)
        if f == 0:
            return "N/A"
        # EODHD returns percentages as decimals (0.245 = 24.5%) OR already as %
        if abs(f) < 1:
            return f"{f * 100:.2f}%"
        return f"{f:.2f}%"
    except Exception:
        return "N/A"


def _resolve_ticker(symbol: str) -> tuple[str, str]:
    """
    Split 'AAPL' → ('AAPL', 'US')
    Also handles explicit exchange: 'TSLA.US' → ('TSLA', 'US')
    """
    if "." in symbol:
        parts = symbol.split(".", 1)
        return parts[0].upper(), parts[1].upper()
    return symbol.upper(), "US"


async def _eodhd_get(path: str, params: dict | None = None) -> dict | list:
    """Make an authenticated GET request to EODHD."""
    _require_clients()
    eodhd_key = os.environ.get("EODHD_API_KEY", "")
    if not eodhd_key:
        raise HTTPException(
            status_code=503,
            detail="EODHD_API_KEY is not set. Add it in Render → Environment.",
        )
    p = {"api_token": eodhd_key, "fmt": "json"}
    if params:
        p.update(params)
    try:
        resp = await _http.get(f"{EODHD_BASE}/{path}", params=p)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"EODHD error: {exc.response.text[:200]}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"EODHD connection error: {exc}") from exc


async def fetch_market_data(symbol: str) -> dict:
    """
    Fetch live quote + fundamentals from EODHD.
    Quote is required. Fundamentals are optional (free tier may not include them).
    """
    cache_key = f"eodhd:{symbol}"
    if cached := await cache_get(cache_key):
        return cached

    ticker, exchange = _resolve_ticker(symbol)
    full_sym = f"{ticker}.{exchange}"

    # ── Fetch quote (required) ────────────────────────────────────────────
    try:
        quote_data = await _eodhd_get(f"real-time/{full_sym}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"EODHD quote failed for {symbol}: {exc}") from exc

    # ── Fetch fundamentals (optional — free tier may not include this) ────
    fund_data = {}
    try:
        fund_data = await _eodhd_get(f"fundamentals/{full_sym}")
        print(f"[STOCK] EODHD fundamentals OK for {symbol}", flush=True)
    except Exception as exc:
        print(f"[STOCK] EODHD fundamentals unavailable for {symbol}: {exc}", flush=True)

    # ── Parse quote ───────────────────────────────────────────────────────
    if isinstance(quote_data, list):
        quote_data = quote_data[0] if quote_data else {}

    price      = float(quote_data.get("close") or quote_data.get("previousClose") or 0)
    prev_close = float(quote_data.get("previousClose") or 0)
    change     = round(float(quote_data.get("change") or 0), 4)
    change_pct = round(float(str(quote_data.get("change_p") or "0").replace("%", "")), 4)
    volume     = int(quote_data.get("volume") or 0)

    # ── Parse fundamentals ────────────────────────────────────────────────
    general    = fund_data.get("General", {})
    highlights = fund_data.get("Highlights", {})
    valuation  = fund_data.get("Valuation", {})
    technicals = fund_data.get("Technicals", {})
    shares     = fund_data.get("SharesStats", {})
    earnings   = fund_data.get("Earnings", {})

    # Analyst ratings
    analyst    = fund_data.get("AnalystRatings", {})

    result = {
        # ── Identity ──────────────────────────────────────────────────
        "symbol":        ticker,
        "name":          _safe(general.get("Name"), ticker),
        "sector":        _safe(general.get("Sector")),
        "industry":      _safe(general.get("Industry")),
        "exchange":      _safe(general.get("Exchange"), exchange),
        "country":       _safe(general.get("CountryName"), "USA"),
        "currency":      _safe(general.get("CurrencyCode"), "USD"),
        "description":   _safe(general.get("Description"), ""),
        "isin":          _safe(general.get("ISIN")),
        "website":       _safe(general.get("WebURL")),

        # ── Quote ─────────────────────────────────────────────────────
        "price":         price,
        "change":        change,
        "change_pct":    str(change_pct),
        "volume":        volume,
        "prev_close":    prev_close,
        "high":          float(quote_data.get("high") or 0),
        "low":           float(quote_data.get("low") or 0),
        "open":          float(quote_data.get("open") or 0),

        # ── Valuation ─────────────────────────────────────────────────
        "market_cap":    _fmt_large(highlights.get("MarketCapitalization")),
        "pe_ratio":      _safe(highlights.get("PERatio")),
        "forward_pe":    _safe(valuation.get("ForwardPE")),
        "peg_ratio":     _safe(highlights.get("PEGRatio")),
        "eps":           _safe(highlights.get("EarningsShare")),
        "eps_growth_yoy":_safe(highlights.get("EPSEstimateNextYear")),
        "book_value":    _safe(highlights.get("BookValue")),
        "price_to_book": _safe(valuation.get("PriceBookMRQ")),
        "price_to_sales":_safe(valuation.get("PriceSalesTTM")),
        "ev_ebitda":     _safe(valuation.get("EnterpriseValueEbitda")),

        # ── Range & Technicals ────────────────────────────────────────
        "52_week_high":  _safe(technicals.get("52WeekHigh")),
        "52_week_low":   _safe(technicals.get("52WeekLow")),
        "50_day_avg":    _safe(technicals.get("50DayMA")),
        "200_day_avg":   _safe(technicals.get("200DayMA")),
        "beta":          _safe(technicals.get("Beta")),
        "short_ratio":   _safe(technicals.get("ShortRatio")),

        # ── Dividends ─────────────────────────────────────────────────
        "div_yield":     _fmt_pct(highlights.get("DividendYield")),
        "div_per_share": _safe(highlights.get("DividendShare")),

        # ── Analyst ───────────────────────────────────────────────────
        "analyst_target":     _safe(highlights.get("AnalystTargetPrice")),
        "analyst_rating":     _safe(analyst.get("Rating")),
        "analyst_buy":        _safe(analyst.get("StrongBuy", 0)),
        "analyst_hold":       _safe(analyst.get("Hold", 0)),
        "analyst_sell":       _safe(analyst.get("StrongSell", 0)),

        # ── Financials ────────────────────────────────────────────────
        "revenue_ttm":        _fmt_large(highlights.get("RevenueTTM")),
        "revenue_per_share":  _safe(highlights.get("RevenuePerShareTTM")),
        "gross_profit_ttm":   _fmt_large(highlights.get("GrossProfitTTM")),
        "ebitda":             _fmt_large(highlights.get("EBITDA")),
        "profit_margin":      _fmt_pct(highlights.get("ProfitMargin")),
        "gross_margin":       _fmt_pct(highlights.get("GrossProfitTTM")),
        "operating_margin":   _fmt_pct(highlights.get("OperatingMarginTTM")),
        "return_on_equity":   _fmt_pct(highlights.get("ReturnOnEquityTTM")),
        "return_on_assets":   _fmt_pct(highlights.get("ReturnOnAssetsTTM")),
        "free_cashflow":      _fmt_large(highlights.get("FreeCashFlow") or
                                         fund_data.get("CashFlow", {}).get("freeCashFlow")),
        "debt_to_equity":     _safe(highlights.get("DebtEquityRatio") or
                                    fund_data.get("Leverage", {}).get("debtEquityRatioTTM")),
        "current_ratio":      _safe(fund_data.get("Leverage", {}).get("currentRatioTTM")),
        "shares_outstanding": _fmt_large(shares.get("SharesOutstanding")),
        "shares_float":       _fmt_large(shares.get("SharesFloat")),

        # ── Meta ──────────────────────────────────────────────────────
        "data_source": "eodhd_live",
    }

    await cache_set(cache_key, result)
    return result


# ── AI market data fallback (when EODHD key missing / rate-limited) ───────────

async def enrich_with_claude(symbol: str) -> dict:
    """Ask Claude to fill in realistic market data from training knowledge."""
    prompt = f"""
Provide realistic and accurate market data for the stock {symbol} based on your training knowledge.
Use the most recent figures you know. Estimate conservatively if uncertain.

Return ONLY this JSON (no markdown):
{{
  "name": "<Full company name>",
  "sector": "<sector>",
  "industry": "<industry>",
  "exchange": "<e.g. NASDAQ>",
  "country": "USA",
  "currency": "USD",
  "price": <number>,
  "change": <number>,
  "change_pct": "<e.g. 0.59>",
  "market_cap": "<e.g. $3.2T>",
  "pe_ratio": "<e.g. 33.2>",
  "forward_pe": "<e.g. 29.5>",
  "peg_ratio": "<e.g. 2.1>",
  "eps": "<e.g. 6.43>",
  "beta": "<e.g. 1.24>",
  "div_yield": "<e.g. 0.52% or N/A>",
  "52_week_high": "<e.g. 237.23>",
  "52_week_low": "<e.g. 164.08>",
  "50_day_avg": "<e.g. 220.5>",
  "200_day_avg": "<e.g. 210.2>",
  "analyst_target": "<e.g. 230.00>",
  "profit_margin": "<e.g. 24.30%>",
  "gross_margin": "<e.g. 45.60%>",
  "operating_margin": "<e.g. 30.10%>",
  "return_on_equity": "<e.g. 160.50%>",
  "return_on_assets": "<e.g. 22.60%>",
  "revenue_ttm": "<e.g. $383B>",
  "ebitda": "<e.g. $130B>",
  "free_cashflow": "<e.g. $90B>",
  "debt_to_equity": "<e.g. 1.87>",
  "current_ratio": "<e.g. 0.95>",
  "price_to_book": "<e.g. 48.5>",
  "book_value": "<e.g. 4.38>",
  "data_source": "ai_estimate"
}}
"""
    try:
        data = await claude_json(prompt, max_tokens=700)
        data["data_source"] = "ai_estimate"
        # Ensure volume and prev_close exist
        data.setdefault("volume",     0)
        data.setdefault("prev_close", 0)
        data.setdefault("high",       0)
        data.setdefault("low",        0)
        return data
    except Exception as exc:
        print(f"[STOCK] enrich_with_claude failed for {symbol}: {exc}", flush=True)
        return {
            "name": symbol, "sector": "N/A", "industry": "N/A",
            "exchange": "N/A", "country": "USA", "currency": "USD",
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
            "volume": 0, "prev_close": 0, "high": 0, "low": 0,
            "data_source": "ai_estimate",
        }


# ── Router ────────────────────────────────────────────────────────────────────
router = APIRouter()


@router.get("/quote/{symbol}", response_model=OkResponse, summary="Live market quote")
async def quote(symbol: str) -> OkResponse:
    try:
        data = await fetch_market_data(symbol.upper())
        keys = ["symbol", "price", "change", "change_pct", "volume", "prev_close", "high", "low", "open"]
        return OkResponse(data={k: data[k] for k in keys if k in data})
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
    description    = "Fetches live data via EODHD then runs Claude AI analysis. Cached 5 min.",
)
async def analyze(symbol: str) -> OkResponse:
    try:
        sym       = symbol.upper()
        cache_key = f"analysis:{sym}"

        if cached := await cache_get(cache_key):
            return OkResponse(data=cached, cached=True)

        # ── Fetch live market data ────────────────────────────────────────
        market:      dict = {}
        data_source: str  = "eodhd_live"

        try:
            market = await fetch_market_data(sym)
            print(f"[STOCK] EODHD data fetched for {sym}", flush=True)
        except Exception as exc:
            print(f"[STOCK] EODHD failed for {sym}: {exc} — falling back to AI estimates", flush=True)
            data_source = "ai_estimate"
            market = await enrich_with_claude(sym)

        data_note = (
            "NOTE: Live market data unavailable — figures are AI estimates from training knowledge."
            if data_source == "ai_estimate" else
            "Data source: EODHD live market data."
        )

        prompt = f"""
Analyze the stock {sym} using the following live market data:
{data_note}

Company       : {market.get('name')}
Sector        : {market.get('sector')} | Industry: {market.get('industry')}
Exchange      : {market.get('exchange')} | Country: {market.get('country')}

── Price ───────────────────────────────────────────────
Current Price : ${market.get('price')}
Change Today  : {market.get('change')} ({market.get('change_pct')}%)
52w High      : {market.get('52_week_high')} | 52w Low: {market.get('52_week_low')}
50d MA        : {market.get('50_day_avg')}  | 200d MA: {market.get('200_day_avg')}
Beta          : {market.get('beta')}

── Valuation ───────────────────────────────────────────
Market Cap    : {market.get('market_cap')}
P/E (TTM)     : {market.get('pe_ratio')} | Forward P/E: {market.get('forward_pe')}
PEG Ratio     : {market.get('peg_ratio')} | Price/Book: {market.get('price_to_book')}
EPS (TTM)     : {market.get('eps')} | Book Value: {market.get('book_value')}
Analyst Target: {market.get('analyst_target')}
Dividend Yield: {market.get('div_yield')}
EV/EBITDA     : {market.get('ev_ebitda')}

── Financials ──────────────────────────────────────────
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

        async def safe_fetch(sym: str) -> tuple[str, dict]:
            try:
                return sym, await fetch_market_data(sym)
            except Exception:
                return sym, await enrich_with_claude(sym)

        pairs   = await asyncio.gather(*[safe_fetch(s) for s in symbols])
        markets = dict(pairs)

        stock_context = "\n".join(
            f"- {sym}: {markets[sym].get('name', sym)}, "
            f"Sector: {markets[sym].get('sector', '?')}, "
            f"Price: ${markets[sym].get('price', '?')}, "
            f"P/E: {markets[sym].get('pe_ratio', '?')}, "
            f"Market Cap: {markets[sym].get('market_cap', '?')}, "
            f"Beta: {markets[sym].get('beta', '?')}, "
            f"Revenue: {markets[sym].get('revenue_ttm', '?')}"
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



# ── NGX Routes (Nigerian Exchange Group) ─────────────────────────────────────

NGX_SYSTEM = (
    "You are a professional Nigerian stock market analyst specializing in NGX "
    "(Nigerian Exchange Group) listed stocks. Always respond with valid JSON only — "
    "no markdown, no preamble, no explanation."
)


async def ngx_claude_json(prompt: str, max_tokens: int = 1000) -> dict:
    """Claude call using NGX-specific system prompt."""
    _require_clients()
    try:
        message = await _anthropic.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = max_tokens,
            system     = NGX_SYSTEM,
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


@router.post("/ngx/analyze", response_model=OkResponse, summary="Analyze an NGX-listed stock")
async def ngx_analyze(body: NgxAnalyzeRequest) -> OkResponse:
    ticker = body.ticker.strip().upper()
    cache_key = f"ngx:{ticker}:{body.analysis_type}"
    cached = await cache_get(cache_key)
    if cached:
        return OkResponse(cached=True, data=cached)

    try:
        prompt = f"""Analyze {ticker} listed on the Nigerian Exchange (NGX).
Analysis type: {body.analysis_type}

Return exactly this JSON structure:
{{
  "ticker": "{ticker}",
  "company": "<full company name>",
  "sector": "<NGX sector>",
  "signal": "BUY" | "HOLD" | "SELL",
  "currentPrice": "<₦XX.XX — use realistic NGX price>",
  "targetPrice": "<₦XX.XX — 12-month analyst target>",
  "upside": "<+XX% or -XX%>",
  "marketCap": "<₦XXXbn>",
  "peRatio": "<XX.X or N/A>",
  "dividendYield": "<X.X% or N/A>",
  "summary": "<2-3 sentence investment analysis>",
  "catalysts": ["<catalyst 1>", "<catalyst 2>", "<catalyst 3>"],
  "risks": ["<risk 1>", "<risk 2>"]
}}
Use realistic NGX data based on your training knowledge. Mark any estimates clearly in the summary."""
        data = await ngx_claude_json(prompt)
        await cache_set(cache_key, data)
        return OkResponse(data=data)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ngx/picks", response_model=OkResponse, summary="AI top picks for an NGX sector")
async def ngx_picks(body: NgxPicksRequest) -> OkResponse:
    cache_key = f"ngx:picks:{body.sector}:{body.signal_filter}"
    cached = await cache_get(cache_key)
    if cached:
        return OkResponse(cached=True, data=cached)

    try:
        signal_instruction = (
            "Include only BUY signals." if body.signal_filter == "BUY"
            else "Include BUY and HOLD signals."
        )
        prompt = f"""Generate top NGX stock picks for {body.sector} sector today.
{signal_instruction}

Return a JSON array of exactly 5 stocks:
[
  {{
    "ticker": "<NGX ticker>",
    "company": "<full company name>",
    "sector": "<sector>",
    "signal": "BUY" | "HOLD",
    "currentPrice": "<₦XX.XX>",
    "targetPrice": "<₦XX.XX>",
    "upside": "<+XX%>",
    "reason": "<one clear sentence explaining the investment case>"
  }}
]
Use realistic NGX-listed companies with genuine investment rationale."""
        data = await ngx_claude_json(prompt, max_tokens=1000)
        picks = data if isinstance(data, list) else data.get("picks", [])
        await cache_set(cache_key, picks)
        return OkResponse(data=picks)

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
        _require_clients()
    except Exception:
        pass
    eodhd_key = os.environ.get("EODHD_API_KEY", "")
    return {
        "ok":              True,
        "service":         "Pipways Stock Terminal",
        "anthropic_ready": _anthropic is not None,
        "http_ready":      _http is not None,
        "eodhd_key_set":   bool(eodhd_key),
        "data_source":     "EODHD live" if eodhd_key else "AI estimates (no EODHD key)",
        "model":           "claude-sonnet-4-6",
    }


# ── Standalone app ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    global _anthropic, _http
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
    _anthropic = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    _http      = httpx.AsyncClient(timeout=15.0)
    print("✓  Pipways Stock Terminal started")
    print(f"   Data source  : {'EODHD live' if EODHD_API_KEY else 'AI estimates (EODHD_API_KEY not set)'}")
    print(f"   Model        : claude-sonnet-4-6")
    yield
    await _http.aclose()
    print("✓  Pipways Stock Terminal shut down")


app = FastAPI(title="Pipways AI Stock Research Terminal", version="4.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router, prefix="/api/stock", tags=["Stock Terminal"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("stock_terminal_backend:app", host="0.0.0.0", port=5050, reload=True)
