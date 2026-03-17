"""
Pipways — Proactive AI Insight Engine
======================================
Module:   backend/ai_insights.py
Endpoint: GET /ai/mentor/insights   (mounted via main.py under /ai/mentor)

Generates deterministic, rule-based insights from live user data:
  • trading journal performance statistics
  • course enrolment & progress
  • active and historical signals
  • (blog content read for future extensibility)

Design principles
-----------------
* Zero external AI API calls — all logic is deterministic Python.
* All DB queries run concurrently via asyncio.gather so the endpoint
  consistently finishes well under the 200 ms budget.
* Non-breaking: the response includes EVERY field that the existing
  loadCoachInsights() JS function reads, so the Mentor sidebar panel
  continues working without any frontend changes.
* Safe: every DB helper wraps in try/except; a missing table or empty
  dataset returns a neutral default — never a 500.
* Maximum 3 prioritised insights returned per call.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends

from .database import database
from .security import get_current_user, get_user_id

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Low-level DB helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _one(sql: str, params: dict = None) -> dict:
    """Fetch one row; return None on any error."""
    try:
        row = await database.fetch_one(sql, params or {})
        return dict(row) if row else None
    except Exception as exc:
        print(f"[AI INSIGHTS] _one error: {exc}", flush=True)
        return None


async def _all(sql: str, params: dict = None) -> list:
    """Fetch all rows; return [] on any error."""
    try:
        rows = await database.fetch_all(sql, params or {})
        return [dict(r) for r in rows] if rows else []
    except Exception as exc:
        print(f"[AI INSIGHTS] _all error: {exc}", flush=True)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Data-fetch layer  (all four run concurrently)
# ─────────────────────────────────────────────────────────────────────────────

async def _fetch_performance(user_id: int) -> dict:
    """
    Pull trade statistics.  Tries the dedicated trade_statistics table first;
    falls back to quiz_attempts as a lightweight proxy when the journal table
    is absent (common on fresh installs).
    """
    stats = await _one(
        """
        SELECT total_trades, win_rate, profit_factor, max_drawdown,
               avg_rr_ratio, net_pnl, winning_streak, losing_streak,
               analyzed_at
        FROM   trade_statistics
        WHERE  user_id = :uid
        ORDER  BY analyzed_at DESC
        LIMIT  1
        """,
        {"uid": user_id},
    )
    if stats:
        return stats

    # Fallback: derive rudimentary stats from quiz attempts
    attempts = await _all(
        """
        SELECT score, passed, attempted_at
        FROM   quiz_attempts
        WHERE  user_id = :uid
        ORDER  BY attempted_at DESC
        LIMIT  20
        """,
        {"uid": user_id},
    )
    if not attempts:
        return {}

    total    = len(attempts)
    passed   = sum(1 for a in attempts if a.get("passed"))
    win_rate = round(passed / total * 100) if total else 0
    avg_score = round(sum(a.get("score", 0) for a in attempts) / total) if total else 0

    # Trend: recent 5 vs previous 5
    recent_wr  = round(sum(1 for a in attempts[:5]   if a.get("passed")) / min(5, total) * 100)
    earlier_wr = round(sum(1 for a in attempts[5:10] if a.get("passed")) / min(5, max(total - 5, 1)) * 100)

    return {
        "total_trades":    total,
        "win_rate":        win_rate,
        "profit_factor":   round(avg_score / 70, 2) if avg_score else 0,
        "max_drawdown":    0,
        "avg_rr_ratio":    0,
        "net_pnl":         0,
        "winning_streak":  0,
        "losing_streak":   0,
        "recent_win_rate": recent_wr,
        "prior_win_rate":  earlier_wr,
        "_source":         "quiz_proxy",
    }


async def _fetch_courses(user_id: int) -> list:
    """Return all courses with user progress percentage."""
    return await _all(
        """
        SELECT c.id, c.title,
               COALESCE(c.lesson_count, 0)       AS total_lessons,
               COALESCE(up.progress_percent, 0)  AS progress_percent,
               COALESCE(up.completed_lessons, 0) AS completed_lessons,
               up.last_accessed
        FROM   courses c
        LEFT   JOIN user_progress up
               ON c.id = up.course_id AND up.user_id = :uid
        WHERE  COALESCE(c.is_active, TRUE) = TRUE
           OR  COALESCE(c.is_published, FALSE) = TRUE
        ORDER  BY up.last_accessed DESC NULLS LAST
        """,
        {"uid": user_id},
    )


async def _fetch_signals() -> list:
    """Return signals from the last 30 days (platform-wide, not user-scoped)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    return await _all(
        """
        SELECT symbol, direction, status, ai_confidence,
               entry_price, stop_loss, take_profit, created_at
        FROM   signals
        WHERE  created_at >= :cutoff
        ORDER  BY created_at DESC
        LIMIT  50
        """,
        {"cutoff": cutoff},
    )


async def _fetch_blog() -> list:
    """Return the three most recent published posts (reserved for future rules)."""
    return await _all(
        """
        SELECT id, title, category, created_at
        FROM   blog_posts
        WHERE  is_published = TRUE
        ORDER  BY created_at DESC
        LIMIT  3
        """,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Insight value object
# ─────────────────────────────────────────────────────────────────────────────

# Priority ordering for the final sort (lower = more urgent)
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class Insight:
    """Lightweight value object for a single generated insight."""

    def __init__(
        self,
        type_,
        title,
        message,
        recommendation,
        priority="medium",
        icon="fa-lightbulb",
        action_label="View details",
        action_target="mentor",
    ):
        self.type           = type_
        self.title          = title
        self.message        = message
        self.recommendation = recommendation
        self.priority       = priority
        self.icon           = icon
        self.action_label   = action_label
        self.action_target  = action_target

    def to_dict(self):
        return {
            "type":           self.type,
            "title":          self.title,
            "message":        self.message,
            "recommendation": self.recommendation,
            "priority":       self.priority,
            "icon":           self.icon,
            "action_label":   self.action_label,
            "action_target":  self.action_target,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based insight generators
# ─────────────────────────────────────────────────────────────────────────────

def _performance_insights(perf: dict) -> list:
    """
    Rules
    -----
    win_rate < 40 %             → risk management warning          (high)
    win_rate 40–54 %            → improvement nudge                (medium)
    recent_wr drops > 12 pts    → declining trend warning          (high)
    max_drawdown > 10 %         → discipline warning               (critical)
    max_drawdown 5–10 %         → caution notice                   (medium)
    profit_factor < 1.0         → losing-system alert              (high)
    losing_streak >= 5          → psychology / break warning       (high)
    """
    if not perf:
        return []

    out = []
    win_rate  = float(perf.get("win_rate")      or 0)
    drawdown  = float(perf.get("max_drawdown")  or 0)
    pf        = float(perf.get("profit_factor") or 0)
    l_streak  = int(perf.get("losing_streak")   or 0)
    recent_wr = float(perf.get("recent_win_rate") or win_rate)
    prior_wr  = float(perf.get("prior_win_rate")  or win_rate)

    # Win rate
    if 0 < win_rate < 40:
        out.append(Insight(
            type_="performance_warning",
            title="Win Rate Needs Attention",
            message=f"Your win rate is {win_rate:.0f}%, below the 40 % threshold.",
            recommendation="Review your entry criteria and risk management rules. "
                           "Consider completing the Risk Management course.",
            priority="high",
            icon="fa-exclamation-triangle",
            action_label="Review Performance",
            action_target="journal",
        ))
    elif 40 <= win_rate < 55:
        out.append(Insight(
            type_="performance_insight",
            title="Win Rate Can Improve",
            message=f"Win rate at {win_rate:.0f}%. "
                    "Small improvements in entry timing could push this above 55 %.",
            recommendation="Study confluence-based entries. "
                           "Review losing trades for repeating patterns.",
            priority="medium",
            icon="fa-chart-line",
            action_label="Analyse Trades",
            action_target="journal",
        ))

    # Declining trend
    if prior_wr > 0 and (prior_wr - recent_wr) >= 12:
        out.append(Insight(
            type_="performance_warning",
            title="Win Rate Declining",
            message=f"Win rate dropped from {prior_wr:.0f} % to {recent_wr:.0f} % in recent trades.",
            recommendation="Step back. Review recent trades for overtrading or strategy deviation.",
            priority="high",
            icon="fa-arrow-trend-down",
            action_label="Review Recent Trades",
            action_target="journal",
        ))

    # Drawdown
    if drawdown > 10:
        out.append(Insight(
            type_="discipline_warning",
            title="High Drawdown Alert",
            message=f"Maximum drawdown is {drawdown:.1f} %, above the 10 % danger threshold.",
            recommendation="Reduce position sizing immediately and review stop-loss placement.",
            priority="critical",
            icon="fa-shield-exclamation",
            action_label="Review Drawdown",
            action_target="journal",
        ))
    elif 5 <= drawdown <= 10:
        out.append(Insight(
            type_="discipline_notice",
            title="Drawdown Rising",
            message=f"Drawdown at {drawdown:.1f} %. Monitor to avoid reaching the 10 % zone.",
            recommendation="Consider reducing risk per trade to 1 % until drawdown recovers.",
            priority="medium",
            icon="fa-triangle-exclamation",
            action_label="Check Risk Rules",
            action_target="journal",
        ))

    # Profit factor
    if 0 < pf < 1.0:
        out.append(Insight(
            type_="performance_warning",
            title="System Running at a Loss",
            message=f"Profit factor of {pf:.2f} means losses currently exceed gains.",
            recommendation="Pause live trading and back-test your strategy. "
                           "Adjust reward-to-risk targets.",
            priority="high",
            icon="fa-circle-minus",
            action_label="Analyse Strategy",
            action_target="analysis",
        ))

    # Losing streak
    if l_streak >= 5:
        out.append(Insight(
            type_="psychology_warning",
            title=f"{l_streak}-Trade Losing Streak",
            message=f"{l_streak} consecutive losses. Trading psychology may be impacted.",
            recommendation="Take a short break. Review your trade checklist and speak with "
                           "the AI Mentor about managing losing streaks.",
            priority="high",
            icon="fa-brain",
            action_label="Talk to AI Mentor",
            action_target="mentor",
        ))

    return out


def _strategy_insights(perf: dict, signals: list) -> list:
    """
    Rules
    -----
    Any active signal with ai_confidence >= 0.70 → highlight the top one  (low)
    One symbol > 60 % of all signals (>= 5 total) → focus recommendation   (low)
    win_rate >= 60 %                               → positive reinforcement (low)
    """
    out = []
    win_rate = float(perf.get("win_rate") or 0) if perf else 0

    # High-confidence active signal
    high_conf = sorted(
        [s for s in signals if s.get("status") == "active"
         and s.get("ai_confidence") and float(s["ai_confidence"]) >= 0.70],
        key=lambda s: float(s["ai_confidence"]),
        reverse=True,
    )
    if high_conf:
        top = high_conf[0]
        conf_pct = round(float(top["ai_confidence"]) * 100)
        out.append(Insight(
            type_="signal_highlight",
            title="High-Confidence Signal Active",
            message=f"{top.get('symbol', 'Unknown')} {top.get('direction', '')} "
                    f"signal has {conf_pct} % AI confidence.",
            recommendation=f"Monitor {top.get('symbol', '')} closely. "
                           "Always verify with your own analysis before entering.",
            priority="low",
            icon="fa-satellite-dish",
            action_label="View Signals",
            action_target="signals",
        ))

    # Dominant symbol
    if len(signals) >= 5:
        sym_counts = {}
        for s in signals:
            sym = (s.get("symbol") or "").upper()
            if sym:
                sym_counts[sym] = sym_counts.get(sym, 0) + 1
        if sym_counts:
            top_sym, top_count = max(sym_counts.items(), key=lambda x: x[1])
            if top_count / len(signals) >= 0.60:
                out.append(Insight(
                    type_="strategy_insight",
                    title=f"Strong Activity on {top_sym}",
                    message=f"{top_sym} accounts for {round(top_count/len(signals)*100)} % "
                            "of recent signals.",
                    recommendation=f"Deepen your knowledge of {top_sym} market dynamics "
                                   "and session patterns.",
                    priority="low",
                    icon="fa-magnifying-glass-chart",
                    action_label="Research Symbol",
                    action_target="stocks",
                ))

    # Positive reinforcement
    if win_rate >= 60:
        out.append(Insight(
            type_="strategy_positive",
            title="Strong Win Rate — Stay Consistent",
            message=f"Win rate of {win_rate:.0f} % is above the 60 % target. "
                    "Focus on consistency.",
            recommendation="Document your current strategy in detail. "
                           "Protect your edge by reviewing what is working.",
            priority="low",
            icon="fa-trophy",
            action_label="Review Strategy",
            action_target="mentor",
        ))

    return out


def _learning_insights(courses: list) -> list:
    """
    Rules
    -----
    No courses started at all          → enrol reminder        (medium)
    Any course < 30 % and in-progress  → stalled course nudge  (medium)
    Any course 30–99 % in-progress     → encourage finish      (low)
    All courses 100 %                  → celebrate + suggest   (low)
    """
    if not courses:
        return []

    out = []
    not_started  = [c for c in courses if (c.get("progress_percent") or 0) == 0]
    in_progress  = [c for c in courses if 0 < (c.get("progress_percent") or 0) < 100]
    completed    = [c for c in courses if (c.get("progress_percent") or 0) == 100]
    low_progress = [c for c in in_progress if (c.get("progress_percent") or 0) < 30]

    # Nothing started
    if not in_progress and not completed and not_started:
        out.append(Insight(
            type_="learning_reminder",
            title="Start Your Learning Journey",
            message=f"{len(not_started)} course{'s' if len(not_started) > 1 else ''} "
                    "available — none started yet.",
            recommendation="Begin with the beginner course. "
                           "Even 15 minutes a day compounds over time.",
            priority="medium",
            icon="fa-graduation-cap",
            action_label="Browse Courses",
            action_target="courses",
        ))
        return out

    # Stalled course
    if low_progress:
        c = low_progress[0]
        pct = c.get("progress_percent") or 0
        out.append(Insight(
            type_="learning_reminder",
            title="Course Progress Stalled",
            message=f"Only {pct} % through '{c.get('title', 'a course')}'. "
                    "Finishing it will noticeably improve your trading skills.",
            recommendation="Schedule 20–30 minutes today to continue. "
                           "Consistent short sessions beat occasional marathons.",
            priority="medium",
            icon="fa-book-open",
            action_label="Continue Course",
            action_target="courses",
        ))

    # Mid-progress encouragement
    elif in_progress and not low_progress:
        c = in_progress[0]
        pct = c.get("progress_percent") or 0
        out.append(Insight(
            type_="learning_progress",
            title="Keep Going — You're Making Progress",
            message=f"{pct} % through '{c.get('title', '')}'. "
                    f"Just {100 - pct} % left to complete it.",
            recommendation="Finish this course before starting another — "
                           "completion improves retention significantly.",
            priority="low",
            icon="fa-circle-half-stroke",
            action_label="Continue Course",
            action_target="courses",
        ))

    # All done
    if completed and not in_progress and not not_started:
        out.append(Insight(
            type_="learning_complete",
            title="All Courses Completed!",
            message=f"You've completed all {len(completed)} available "
                    f"course{'s' if len(completed) > 1 else ''}. Outstanding.",
            recommendation="Apply your knowledge — review your trade journal and "
                           "discuss patterns with the AI Mentor.",
            priority="low",
            icon="fa-medal",
            action_label="Talk to AI Mentor",
            action_target="mentor",
        ))

    return out


def _signal_insights(signals: list) -> list:
    """
    Rules
    -----
    > 10 active signals             → signal overload notice           (medium)
    Zero signals in last 7 days     → quiet market notice              (low)
    Symbol with >= 3 closed signals
      and win-rate proxy >= 72 %    → high-performing symbol highlight (low)
    """
    if not signals:
        return []

    out = []
    active = [s for s in signals if s.get("status") == "active"]

    # Overload
    if len(active) > 10:
        out.append(Insight(
            type_="signal_notice",
            title="High Signal Volume",
            message=f"{len(active)} active signals right now. "
                    "High volume can indicate choppy conditions.",
            recommendation="Be selective. Only trade setups that meet your full checklist.",
            priority="medium",
            icon="fa-filter",
            action_label="View Signals",
            action_target="signals",
        ))

    # Quiet market
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_any = [
        s for s in signals
        if s.get("created_at") and _parse_dt(s["created_at"]) >= week_ago
    ]
    if not recent_any:
        out.append(Insight(
            type_="signal_notice",
            title="Quiet Signal Period",
            message="No new signals posted in the last 7 days.",
            recommendation="Use the quiet period to focus on education and strategy review.",
            priority="low",
            icon="fa-satellite-dish",
            action_label="Study Strategy",
            action_target="courses",
        ))

    # High-performing closed symbol
    closed = [s for s in signals if s.get("status") == "closed"]
    if closed:
        sym_stats = {}
        for s in closed:
            sym = (s.get("symbol") or "").upper()
            if not sym:
                continue
            if sym not in sym_stats:
                sym_stats[sym] = {"total": 0, "win": 0}
            sym_stats[sym]["total"] += 1
            try:
                tp    = float(s.get("take_profit") or 0)
                entry = float(s.get("entry_price") or 0)
                is_buy = (s.get("direction") or "").upper() == "BUY"
                if entry > 0 and tp > 0:
                    won = (tp > entry) if is_buy else (tp < entry)
                    if won:
                        sym_stats[sym]["win"] += 1
            except (TypeError, ValueError):
                pass

        for sym, st in sym_stats.items():
            if st["total"] >= 3:
                wr = round(st["win"] / st["total"] * 100)
                if wr >= 72:
                    out.append(Insight(
                        type_="signal_highlight",
                        title=f"{sym} Showing Strong Results",
                        message=f"{sym} signals have a {wr} % win rate "
                                f"across {st['total']} recent trades.",
                        recommendation=f"Monitor {sym} setups. "
                                       "Review the signal methodology in Chart Analysis.",
                        priority="low",
                        icon="fa-star",
                        action_label="View Signals",
                        action_target="signals",
                    ))
                    break   # only one symbol highlight per call

    return out


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation & deduplication
# ─────────────────────────────────────────────────────────────────────────────

def _select_top(candidates: list, max_count: int = 3) -> list:
    """
    Sort by priority (critical > high > medium > low), deduplicate on type
    prefix (so we never return two 'performance_*' or two 'learning_*'
    insights), then return at most max_count.
    """
    candidates.sort(key=lambda i: _PRIORITY_ORDER.get(i.priority, 99))
    seen = set()
    result = []
    for insight in candidates:
        prefix = insight.type.split("_")[0]
        if prefix not in seen:
            seen.add(prefix)
            result.append(insight)
        if len(result) >= max_count:
            break
    return result


def _parse_dt(value: Any) -> datetime:
    """Parse any datetime-like value to a UTC-aware datetime."""
    try:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(value)).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Profile derivation  (powers the Mentor sidebar panel)
# ─────────────────────────────────────────────────────────────────────────────

def _derive_profile(perf: dict, courses: list, signals: list) -> dict:
    """
    Build the full mentor-panel profile expected by loadCoachInsights():
      trading_personality, discipline_score, consistency_score,
      risk_profile, strengths, weaknesses,
      recommended_next_steps, recommended_resources.

    Entirely deterministic — no AI calls.
    """
    win_rate    = float(perf.get("win_rate")      or 0) if perf else 0
    pf          = float(perf.get("profit_factor") or 0) if perf else 0
    drawdown    = float(perf.get("max_drawdown")  or 0) if perf else 0
    total_trades = int(perf.get("total_trades")   or 0) if perf else 0
    l_streak    = int(perf.get("losing_streak")   or 0) if perf else 0

    # ── Trading personality ───────────────────────────────────────────────
    if total_trades == 0:
        personality = "New Learner"
    elif win_rate >= 60 and pf >= 1.5:
        personality = "Disciplined Trader"
    elif win_rate >= 50:
        personality = "Developing Trader"
    elif drawdown > 10 or l_streak >= 5:
        personality = "High-Risk Trader"
    else:
        personality = "Learning Trader"

    # ── Discipline score (0–100) ──────────────────────────────────────────
    discipline_score = min(100, max(0, (
        50
        + (15 if win_rate >= 50 else -15 if win_rate > 0 else 0)
        + (15 if pf >= 1.2     else -10 if 0 < pf < 1 else 0)
        + (-20 if drawdown > 10 else -10 if drawdown > 5 else 10)
        + (-15 if l_streak >= 5 else 5 if l_streak == 0 else 0)
    )))

    # ── Consistency score (0–100) ─────────────────────────────────────────
    course_avg = 0
    if courses:
        course_avg = sum(c.get("progress_percent") or 0 for c in courses) / len(courses)
    consistency_score = min(100, max(0, (
        40
        + (20 if course_avg >= 70 else 10 if course_avg >= 40 else 0)
        + (20 if win_rate >= 55   else 10 if win_rate >= 45 else 0)
        + (20 if pf >= 1.3 else 0)
    )))

    # ── Risk profile ──────────────────────────────────────────────────────
    if drawdown > 15 or l_streak >= 7:
        risk_profile = "Aggressive"
    elif drawdown > 8 or l_streak >= 4:
        risk_profile = "Moderately Aggressive"
    elif win_rate >= 55 and pf >= 1.3:
        risk_profile = "Conservative"
    else:
        risk_profile = "Moderate"

    # ── Strengths ─────────────────────────────────────────────────────────
    strengths = []
    if win_rate >= 55:
        strengths.append(f"Consistent win rate of {win_rate:.0f} %")
    if pf >= 1.5:
        strengths.append(f"Good profit factor ({pf:.1f}x)")
    if course_avg >= 60:
        strengths.append("Active commitment to structured learning")
    if not strengths:
        strengths.append(
            "Actively tracking performance" if total_trades > 0
            else "Starting the learning journey"
        )
    active_signals = sum(1 for s in signals if s.get("status") == "active")
    if active_signals:
        strengths.append(f"Staying informed with {active_signals} active signals")

    # ── Weaknesses ────────────────────────────────────────────────────────
    weaknesses = []
    if 0 < win_rate < 45:
        weaknesses.append(f"Win rate below 45 % ({win_rate:.0f} %)")
    if 0 < pf < 1.0:
        weaknesses.append("Losses currently exceeding gains")
    if drawdown > 5:
        weaknesses.append(f"Drawdown at {drawdown:.1f} % needs attention")
    if l_streak >= 3:
        weaknesses.append(f"{l_streak}-trade losing streak")
    if course_avg < 30 and courses:
        weaknesses.append("Course completion below 30 %")
    if not weaknesses:
        weaknesses.append("Continue analysing trades for improvement areas")

    # ── Recommended next steps ────────────────────────────────────────────
    next_steps = []
    incomplete  = [c for c in courses if 0 < (c.get("progress_percent") or 0) < 100]
    not_started = [c for c in courses if (c.get("progress_percent") or 0) == 0]

    if incomplete:
        next_steps.append(f"Finish '{incomplete[0].get('title', 'your current course')}'")
    elif not_started:
        next_steps.append(f"Begin '{not_started[0].get('title', 'an available course')}'")
    if 0 < win_rate < 50:
        next_steps.append("Review and tighten your entry criteria")
    if drawdown > 5:
        next_steps.append("Reduce position size until drawdown recovers")
    if not next_steps:
        next_steps.append("Keep a trade journal entry for every trade")
    next_steps.append("Ask the AI Mentor for a personalised strategy review")

    # ── Recommended resources ─────────────────────────────────────────────
    resources = []
    if 0 < win_rate < 50:
        resources.append({
            "type": "course",
            "title": "Risk Management Essentials",
            "description": "Learn position sizing, stop-loss rules and risk-reward ratios.",
        })
    if incomplete:
        resources.append({
            "type": "course",
            "title": incomplete[0]["title"],
            "description": "Continue your structured learning path.",
        })
    elif not_started and courses:
        resources.append({
            "type": "course",
            "title": not_started[0]["title"],
            "description": "Start this course to build your trading foundation.",
        })
    if active_signals:
        resources.append({
            "type": "signal",
            "title": "Review Active Signals",
            "description": "Analyse current setups against your own chart reading.",
        })
    if not resources:
        resources.append({
            "type": "strategy",
            "title": "Strategy Consistency Review",
            "description": "Evaluate whether recent trades followed your system rules.",
        })

    return {
        "trading_personality":    personality,
        "discipline_score":       int(discipline_score),
        "consistency_score":      int(consistency_score),
        "risk_profile":           risk_profile,
        "strengths":              strengths[:3],
        "weaknesses":             weaknesses[:3],
        "recommended_next_steps": next_steps[:4],
        "recommended_resources":  resources[:3],
    }


# ─────────────────────────────────────────────────────────────────────────────
# API endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/insights")
async def get_insights(current_user=Depends(get_current_user)):
    """
    GET /ai/mentor/insights

    Returns a rich, sub-200 ms payload combining:
      • Full mentor-panel profile  (loadCoachInsights reads these directly)
      • insights[]                 up to 3 prioritised dashboard insights
      • meta                       timing, data-freshness flags
    """
    t0      = time.monotonic()
    user_id = get_user_id(current_user)

    # All four data sources run concurrently; exceptions fall back to empty
    results = await asyncio.gather(
        _fetch_performance(user_id),
        _fetch_courses(user_id),
        _fetch_signals(),
        _fetch_blog(),
        return_exceptions=True,
    )
    perf    = results[0] if not isinstance(results[0], Exception) else {}
    courses = results[1] if not isinstance(results[1], Exception) else []
    signals = results[2] if not isinstance(results[2], Exception) else []
    # blog unused in rules currently but fetched for future extensibility

    # Generate all candidate insights from every rule set
    candidates = (
        _performance_insights(perf)
        + _strategy_insights(perf, signals)
        + _learning_insights(courses)
        + _signal_insights(signals)
    )

    top = _select_top(candidates, max_count=3)
    profile = _derive_profile(perf, courses, signals)
    elapsed_ms = round((time.monotonic() - t0) * 1000, 1)

    print(
        f"[AI INSIGHTS] user={user_id} candidates={len(candidates)} "
        f"returned={len(top)} elapsed={elapsed_ms}ms",
        flush=True,
    )

    return {
        # Mentor sidebar fields — read verbatim by loadCoachInsights()
        **profile,

        # Dashboard insight list
        "insights": [i.to_dict() for i in top],

        # Debugging / cache metadata
        "meta": {
            "generated_at":  datetime.now(timezone.utc).isoformat(),
            "elapsed_ms":    elapsed_ms,
            "has_perf_data": bool(perf),
            "has_courses":   bool(courses),
            "signal_count":  len(signals),
            "insight_count": len(top),
        },
    }
