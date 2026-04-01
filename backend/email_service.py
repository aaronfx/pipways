"""
Email Service for Gopipways
Handles: welcome emails, lesson completion, signal alerts, weekly digest

Provider: Brevo (formerly Sendinblue) — HTTPS API, works on Railway.
  Railway blocks outbound SMTP ports 465/587. Brevo uses HTTPS so it
  is never blocked.

Environment variables:
  EMAIL_PROVIDER        — "brevo" (recommended) | "smtp" | "mailgun"
  BREVO_API_KEY         — your Brevo API key (starts with xkeysib-)
  EMAIL_FROM_NAME       — "Gopipways" (default)
  EMAIL_FROM_ADDRESS    — contact@gopipways.com
  APP_BASE_URL          — https://www.gopipways.com

  SMTP fallback (only if EMAIL_PROVIDER=smtp):
  SMTP_HOST             — mail.spacemail.com
  SMTP_PORT             — 587 or 465
  SMTP_USER             — contact@gopipways.com
  SMTP_PASSWORD         — your SpaceMail password
"""

import os
import re
import json
import bcrypt
import secrets
import httpx
import asyncio
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr

from .database import database
from .security import get_current_user, get_user_id, is_admin_user

router = APIRouter()

EMAIL_PROVIDER  = os.getenv("EMAIL_PROVIDER", "brevo")
BREVO_API_KEY   = os.getenv("BREVO_API_KEY", "")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN  = os.getenv("MAILGUN_DOMAIN", "")
SMTP_HOST       = os.getenv("SMTP_HOST", "mail.spacemail.com")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER       = os.getenv("SMTP_USER", "contact@gopipways.com")
SMTP_PASSWORD   = os.getenv("SMTP_PASSWORD", "")
FROM_NAME       = os.getenv("EMAIL_FROM_NAME", "Gopipways")
FROM_ADDRESS    = os.getenv("EMAIL_FROM_ADDRESS", "contact@gopipways.com")
APP_BASE_URL    = os.getenv("APP_BASE_URL", "https://www.gopipways.com")


# ── Table initialisation ───────────────────────────────────────────────────────

async def ensure_email_tables():
    """Create email-related tables if they don't exist. Called from main.py lifespan."""
    statements = [
        """CREATE TABLE IF NOT EXISTS email_logs (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER,
            email_type VARCHAR(50),
            to_email   VARCHAR(255),
            success    BOOLEAN DEFAULT FALSE,
            sent_at    TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS email_subscribers (
            id              SERIAL PRIMARY KEY,
            email           VARCHAR(255) UNIQUE NOT NULL,
            name            VARCHAR(255),
            source          VARCHAR(50),
            subscribed_at   TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS user_email_preferences (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER UNIQUE NOT NULL,
            preferences TEXT,
            updated_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            email       VARCHAR(255) NOT NULL,
            token       VARCHAR(128) UNIQUE NOT NULL,
            expires_at  TIMESTAMP NOT NULL,
            used        BOOLEAN DEFAULT FALSE,
            created_at  TIMESTAMP DEFAULT NOW()
        )""",
        """CREATE INDEX IF NOT EXISTS idx_reset_tokens_token
           ON password_reset_tokens(token)""",
        """CREATE INDEX IF NOT EXISTS idx_reset_tokens_email
           ON password_reset_tokens(email)""",
    ]
    ok = 0
    for stmt in statements:
        try:
            await database.execute(stmt)
            ok += 1
        except Exception as e:
            print(f"[EMAIL TABLES] Warning: {e}", flush=True)
    print(f"[EMAIL] Tables ready ({ok}/{len(statements)} ok)", flush=True)


# ── Core send ──────────────────────────────────────────────────────────────────

async def send_email(to_email: str, subject: str, html_body: str,
                     text_body: Optional[str] = None) -> bool:
    if not to_email:
        return False
    from_field = f"{FROM_NAME} <{FROM_ADDRESS}>"
    text_body  = text_body or re.sub(r"<[^>]+>", "", html_body).strip()
    try:
        if EMAIL_PROVIDER == "brevo" and BREVO_API_KEY:
            return await _send_brevo(to_email, subject, html_body, text_body)
        elif EMAIL_PROVIDER == "mailgun" and MAILGUN_API_KEY and MAILGUN_DOMAIN:
            return await _send_mailgun(to_email, from_field, subject, html_body, text_body)
        elif SMTP_USER and SMTP_PASSWORD:
            return await _send_smtp(to_email, from_field, subject, html_body, text_body)
        else:
            print(f"[EMAIL] No provider configured — skipping email to {to_email}", flush=True)
            return False
    except Exception as e:
        print(f"[EMAIL] Send failed to {to_email}: {e}", flush=True)
        return False


async def _send_brevo(to_email: str, subject: str, html: str, text: str) -> bool:
    """
    Send via Brevo (formerly Sendinblue) Transactional Email API.
    Uses HTTPS — not blocked by Railway unlike SMTP ports 465/587.
    Docs: https://developers.brevo.com/reference/sendtransacemail
    """
    if not BREVO_API_KEY:
        print("[EMAIL/Brevo] ❌ BREVO_API_KEY is not set — check Railway variables", flush=True)
        return False

    payload = {
        "sender":      {"name": FROM_NAME, "email": FROM_ADDRESS},
        "to":          [{"email": to_email}],
        "subject":     subject,
        "htmlContent": html,
        "textContent": text,
    }

    print(f"[EMAIL/Brevo] Sending to={to_email} from={FROM_ADDRESS} subject={subject[:40]}", flush=True)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key":      BREVO_API_KEY,
                    "Content-Type": "application/json",
                    "Accept":       "application/json",
                },
                json=payload,
            )

        if res.status_code in (200, 201):
            print(f"[EMAIL/Brevo] ✅ Sent to {to_email}: {subject[:40]}", flush=True)
            return True

        # Log the full Brevo error response so we can diagnose
        print(f"[EMAIL/Brevo] ❌ HTTP {res.status_code}: {res.text}", flush=True)

        # Common Brevo error codes
        if res.status_code == 401:
            print("[EMAIL/Brevo] ❌ Invalid API key — check BREVO_API_KEY in Railway variables", flush=True)
        elif res.status_code == 400:
            print("[EMAIL/Brevo] ❌ Bad request — sender email may not be verified in Brevo", flush=True)
            print("[EMAIL/Brevo]    → Go to brevo.com → Senders & Domains → verify contact@gopipways.com", flush=True)
        elif res.status_code == 403:
            print("[EMAIL/Brevo] ❌ Forbidden — account may be restricted or sender not approved", flush=True)

        return False

    except httpx.TimeoutException:
        print("[EMAIL/Brevo] ❌ Timeout connecting to Brevo API", flush=True)
        return False
    except Exception as e:
        print(f"[EMAIL/Brevo] ❌ Exception: {type(e).__name__}: {e}", flush=True)
        return False


async def _send_mailgun(to, from_field, subject, html, text) -> bool:
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={"from": from_field, "to": [to], "subject": subject,
                  "html": html, "text": text},
        )
    if res.status_code not in (200, 201):
        print(f"[EMAIL/Mailgun] {res.status_code} {res.text}", flush=True)
        return False
    return True


async def _send_smtp(to, from_field, subject, html, text) -> bool:
    def _sync():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = from_field
        msg["To"]      = to
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html,  "html"))
        # Timeout of 15s prevents hanging forever on blocked ports
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as s:
                s.login(SMTP_USER, SMTP_PASSWORD)
                s.sendmail(FROM_ADDRESS, [to], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(SMTP_USER, SMTP_PASSWORD)
                s.sendmail(FROM_ADDRESS, [to], msg.as_string())
        return True

    try:
        return await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _sync),
            timeout=20.0   # hard 20s ceiling — prevents request hanging forever
        )
    except asyncio.TimeoutError:
        print(f"[EMAIL/SMTP] Timeout connecting to {SMTP_HOST}:{SMTP_PORT} — "
              f"port may be blocked by Railway. Try port 465 or use a relay service.", flush=True)
        return False
    except smtplib.SMTPAuthenticationError as e:
        print(f"[EMAIL/SMTP] Authentication failed — check SMTP_USER and SMTP_PASSWORD: {e}", flush=True)
        return False
    except smtplib.SMTPConnectError as e:
        print(f"[EMAIL/SMTP] Cannot connect to {SMTP_HOST}:{SMTP_PORT}: {e}", flush=True)
        return False
    except Exception as e:
        print(f"[EMAIL/SMTP] Error: {type(e).__name__}: {e}", flush=True)
        return False


# ── Base template ─────────────────────────────────────────────────────────────

def _base(content: str, preview: str = "") -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;">{preview}</div>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:40px 20px;">
<tr><td align="center"><table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;">
<tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:32px 40px;border-radius:12px 12px 0 0;text-align:center;">
  <h1 style="margin:0;color:white;font-size:24px;font-weight:800;">📈 Gopipways</h1>
  <p style="margin:4px 0 0;color:rgba(255,255,255,.8);font-size:13px;">Professional Trading Platform</p>
</td></tr>
<tr><td style="background:white;padding:36px 40px;">{content}</td></tr>
<tr><td style="background:#f9fafb;padding:20px 40px;border-radius:0 0 12px 12px;text-align:center;border-top:1px solid #e5e7eb;">
  <p style="margin:0;font-size:12px;color:#9ca3af;">
    You're receiving this because you signed up at Gopipways.<br>
    <a href="{APP_BASE_URL}/dashboard.html" style="color:#6b7280;">Manage email preferences</a>
  </p>
</td></tr>
</table></td></tr></table></body></html>"""


# ── Templates ──────────────────────────────────────────────────────────────────

def welcome_email(full_name: str) -> tuple:
    first = (full_name or "Trader").split()[0]
    content = f"""
<h2 style="margin:0 0 8px;font-size:22px;color:#111827;">You're in, {first}. Your edge starts now. 🚀</h2>

<p style="color:#374151;line-height:1.7;margin:0 0 20px;font-size:15px;">
  Most retail traders lose money — not because they're not smart, but because they're
  trading blind against institutions. <strong>Today that changes.</strong>
  You now have the same analytical tools used by professional desks, at a fraction of the cost.
</p>

<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin-bottom:24px;">
  <p style="margin:0;font-size:14px;color:#166534;line-height:1.6;">
    💡 <strong>Start here:</strong> Go to the Trading Academy and complete Module 1 — SMC Foundations.
    Once you understand the structure, every live signal will make complete sense.
  </p>
</div>

<p style="color:#374151;font-size:14px;font-weight:600;margin:0 0 12px;">Everything included in your account:</p>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:11px 8px;">
      <strong style="color:#111827;">📚 Trading Academy</strong><br>
      <span style="color:#6b7280;font-size:13px;">SMC curriculum from zero to advanced — quizzes, progress tracking and certificates. Free forever.</span>
    </td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:11px 8px;">
      <strong style="color:#111827;">📊 Live Trading Signals</strong><br>
      <span style="color:#6b7280;font-size:13px;">Institutional-grade SMC signals with entry, stop loss, take profit, R:R ratio and full trade rationale.</span>
    </td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:11px 8px;">
      <strong style="color:#111827;">🔍 AI Chart Analysis</strong><br>
      <span style="color:#6b7280;font-size:13px;">Upload any chart and get instant institutional analysis — order blocks, fair value gaps, market bias and trade setup.</span>
    </td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:11px 8px;">
      <strong style="color:#111827;">💰 Risk Calculator</strong><br>
      <span style="color:#6b7280;font-size:13px;">Calculate exact position sizes and lot sizes for any instrument. Never risk the wrong amount again.</span>
    </td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:11px 8px;">
      <strong style="color:#111827;">📈 NGX Stock Terminal</strong><br>
      <span style="color:#6b7280;font-size:13px;">Research Nigerian stocks with live prices, AI-generated estimates and full sector analysis.</span>
    </td>
  </tr>
  <tr>
    <td style="padding:11px 8px;">
      <strong style="color:#111827;">🤖 AI Trading Mentor</strong><br>
      <span style="color:#6b7280;font-size:13px;">Ask any trading question — SMC concepts, setups, risk management — and get expert answers instantly.</span>
    </td>
  </tr>
</table>

<div style="text-align:center;margin-bottom:24px;">
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);color:white;
            text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;">
    Start Your First Lesson — It's Free →
  </a>
</div>

<p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.6;">
  We're in your corner. Reply to this email anytime — we read every message personally.<br>
  Or reach us at <a href="mailto:contact@gopipways.com" style="color:#667eea;">contact@gopipways.com</a>
</p>"""
    return ("You're in — your trading edge starts now 🚀",
            _base(content, f"{first}, most traders fail because they lack the right tools. You just fixed that."))


def lesson_complete_email(full_name: str, lesson_title: str, module_title: str,
                           next_lesson: Optional[str] = None,
                           lesson_number: int = 0, total_lessons: int = 0) -> tuple:
    first = (full_name or "Trader").split()[0]
    progress_text = f"Lesson {lesson_number} of {total_lessons}" if lesson_number and total_lessons else module_title
    progress_pct  = int((lesson_number / total_lessons) * 100) if lesson_number and total_lessons else 0

    progress_bar = f"""
<div style="margin:16px 0;">
  <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
    <span style="font-size:12px;color:#6b7280;">{progress_text}</span>
    {f'<span style="font-size:12px;color:#667eea;font-weight:600;">{progress_pct}% complete</span>' if progress_pct else ''}
  </div>
  {f'<div style="background:#e5e7eb;border-radius:9999px;height:6px;"><div style="background:linear-gradient(90deg,#667eea,#764ba2);height:6px;border-radius:9999px;width:{progress_pct}%;"></div></div>' if progress_pct else ''}
</div>""" if progress_pct else ""

    next_block = f"""
<div style="background:#eff6ff;border-radius:8px;padding:16px;margin:20px 0;border-left:4px solid #3b82f6;">
  <p style="margin:0 0 4px;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;">Up Next</p>
  <p style="margin:0 0 12px;font-size:15px;color:#1e40af;font-weight:600;">{next_lesson}</p>
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:#3b82f6;color:white;text-decoration:none;
            padding:10px 20px;border-radius:6px;font-size:14px;font-weight:600;">
    Continue Learning →
  </a>
</div>
<p style="font-size:12px;color:#9ca3af;margin:0;text-align:center;font-style:italic;">
  Traders who stop here rarely come back. The ones who don't — trade differently.
</p>""" if next_lesson else f"""
<div style="text-align:center;margin:20px 0;">
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:#3b82f6;color:white;text-decoration:none;
            padding:12px 24px;border-radius:8px;font-size:14px;font-weight:600;">
    Go to Academy →
  </a>
</div>"""

    content = f"""
<div style="background:#f0fdf4;border-left:4px solid #10b981;border-radius:0 8px 8px 0;
            padding:14px 16px;margin-bottom:20px;">
  <p style="margin:0;font-size:14px;color:#166534;font-weight:600;line-height:1.5;">
    {first} — you just did what most people never do. You showed up and learned.
    That discipline is the real edge in trading.
  </p>
</div>

<p style="color:#374151;margin:0 0 4px;font-size:14px;">You completed:</p>
<div style="background:#f8fafc;border-radius:8px;padding:16px;margin:12px 0 0;border-left:4px solid #10b981;">
  <p style="margin:0;font-size:13px;color:#6b7280;">{module_title}</p>
  <p style="margin:4px 0 0;font-size:17px;font-weight:700;color:#111827;">{lesson_title}</p>
  {progress_bar}
</div>

{next_block}"""
    return (f"✅ {first}, you're building the habits most traders never will",
            _base(content, f"One lesson closer to trading with confidence. Here's what's next."))


def certificate_email(full_name: str, course_title: str, cert_number: str) -> tuple:
    first = (full_name or "Trader").split()[0]
    content = f"""
<div style="text-align:center;margin-bottom:24px;">
  <div style="font-size:64px;line-height:1;">🏆</div>
  <h2 style="margin:16px 0 8px;font-size:26px;color:#111827;font-weight:800;">
    {first}, you've done what most traders never do.
  </h2>
  <p style="color:#374151;margin:0;font-size:15px;line-height:1.6;">
    You finished. Most people start a course and quit at Lesson 3.<br>
    You didn't. That discipline will show up in your trading.
  </p>
</div>

<div style="background:linear-gradient(135deg,#fefce8,#fffbeb);border:2px solid #fde68a;
            border-radius:12px;padding:28px;text-align:center;margin-bottom:24px;">
  <p style="margin:0 0 8px;font-size:12px;color:#92400e;text-transform:uppercase;letter-spacing:.08em;">
    Certificate of Completion
  </p>
  <p style="margin:0 0 12px;font-size:20px;font-weight:800;color:#111827;">{course_title}</p>
  <p style="margin:0;font-size:13px;color:#b45309;font-family:monospace;letter-spacing:.05em;">
    Certificate ID: <strong>{cert_number}</strong>
  </p>
</div>

<p style="color:#374151;line-height:1.7;margin:0 0 16px;font-size:14px;">
  You now understand SMC concepts that 90% of retail traders will never learn.
  That's not an exaggeration — most traders never take the time to study properly.
  You've joined a small group of certified Gopipways traders who have.
</p>

<div style="background:#f8fafc;border-radius:8px;padding:16px;margin-bottom:24px;border-left:4px solid #667eea;">
  <p style="margin:0;font-size:13px;color:#374151;font-weight:600;">What's next?</p>
  <p style="margin:6px 0 0;font-size:13px;color:#6b7280;">
    Put your knowledge to work. Check today's live signals and apply what you've learned.
  </p>
</div>

<div style="text-align:center;margin-bottom:20px;display:grid;grid-template-columns:1fr 1fr;gap:12px;">
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);color:white;
            text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:700;font-size:14px;">
    View My Certificate →
  </a>
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:#111827;color:white;
            text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:700;font-size:14px;">
    See Live Signals →
  </a>
</div>

<p style="font-size:13px;color:#9ca3af;text-align:center;">
  Share your achievement — you've earned it.
</p>"""
    return (f"🏆 {first}, you've done what most traders never do — you finished.",
            _base(content, f"Your certificate is ready. And your trading will never be the same."))


def new_signal_email(full_name: str, symbol: str, direction: str,
                     entry: float, sl: float, tp: float,
                     confidence: int = 0, timeframe: str = "H1",
                     rationale: str = "") -> tuple:
    first     = (full_name or "Trader").split()[0]
    color     = "#16a34a" if direction.upper() == "BUY" else "#dc2626"
    bg_color  = "#f0fdf4" if direction.upper() == "BUY" else "#fef2f2"
    dir_label = "🟢 BUY" if direction.upper() == "BUY" else "🔴 SELL"
    rr        = round(abs(tp - entry) / abs(entry - sl), 2) if abs(entry - sl) > 0 else 0
    conf_label = f"{confidence}%" if confidence else ""

    rationale_block = f"""
<div style="background:#f8fafc;border-radius:8px;padding:16px;margin:16px 0;border-left:4px solid #6b7280;">
  <p style="margin:0 0 4px;font-size:12px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;">Why This Setup</p>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">{rationale}</p>
</div>""" if rationale else ""

    confidence_row = f"""
  <tr style="background:#f9fafb;">
    <td style="padding:10px 14px;font-weight:600;color:#374151;">Confidence</td>
    <td style="padding:10px 14px;font-weight:700;color:#7c3aed;">{conf_label}</td>
  </tr>""" if confidence else ""

    content = f"""
<div style="background:#111827;border-radius:10px;padding:16px 20px;
            margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;">
  <div>
    <p style="margin:0;font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;">Signal Active</p>
    <p style="margin:4px 0 0;font-size:13px;color:#fbbf24;font-weight:600;">
      ⚡ Price is approaching the entry zone — act before the window closes
    </p>
  </div>
</div>

<div style="background:{bg_color};border:1px solid {color}33;border-radius:10px;
            padding:20px;text-align:center;margin-bottom:20px;">
  <p style="margin:0 0 4px;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.06em;">Institutional Setup</p>
  <h2 style="margin:0;font-size:30px;font-weight:800;color:#111827;">{symbol}</h2>
  <p style="margin:8px 0 0;font-size:20px;font-weight:700;color:{color};">{dir_label}</p>
  {f'<p style="margin:6px 0 0;font-size:13px;color:#7c3aed;font-weight:600;">{timeframe} · {conf_label} Confidence</p>' if confidence else f'<p style="margin:6px 0 0;font-size:13px;color:#6b7280;">{timeframe}</p>'}
</div>

<table width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e5e7eb;border-radius:8px;margin-bottom:16px;overflow:hidden;">
  <tr>
    <td style="padding:11px 14px;font-weight:600;color:#374151;">Entry Price</td>
    <td style="padding:11px 14px;font-weight:700;color:#111827;font-size:16px;">{entry}</td>
  </tr>
  <tr style="background:#f9fafb;">
    <td style="padding:11px 14px;font-weight:600;color:#374151;">Stop Loss</td>
    <td style="padding:11px 14px;font-weight:700;color:#dc2626;">{sl}</td>
  </tr>
  <tr>
    <td style="padding:11px 14px;font-weight:600;color:#374151;">Take Profit</td>
    <td style="padding:11px 14px;font-weight:700;color:#16a34a;">{tp}</td>
  </tr>
  <tr style="background:#f9fafb;">
    <td style="padding:11px 14px;font-weight:600;color:#374151;">Risk:Reward</td>
    <td style="padding:11px 14px;font-weight:700;color:#7c3aed;">1:{rr}</td>
  </tr>
  {confidence_row}
</table>

{rationale_block}

<div style="text-align:center;margin:20px 0 16px;">
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:{color};color:white;
            text-decoration:none;padding:13px 32px;border-radius:8px;font-weight:700;font-size:15px;">
    Open Full Analysis Before the Window Closes →
  </a>
</div>

<p style="margin:0;font-size:11px;color:#9ca3af;text-align:center;line-height:1.6;">
  This is not financial advice. Always apply proper risk management.<br>
  Only risk capital you can afford to lose.
</p>"""
    return (f"⚡ {direction.upper()} Signal: {symbol} — Institutional setup active | {timeframe}",
            _base(content, f"Smart money just moved. {symbol} {direction.upper()} — Entry {entry}, targeting {tp}."))


def subscription_email(full_name: str, plan: str, amount: str,
                       billing_cycle: str = "monthly") -> tuple:
    first = (full_name or "Trader").split()[0]
    plan_label = plan.upper()
    features = {
        "pro": [
            "📊 Unlimited live trading signals with full SMC rationale",
            "🔍 AI Chart Analysis — unlimited chart uploads per day",
            "📈 Advanced performance analytics and trade journal",
            "🤖 Priority AI Mentor — faster responses, deeper analysis",
            "📚 Full Trading Academy with all advanced modules",
            "🔔 Instant signal alerts via email and dashboard",
        ],
        "basic": [
            "📊 Live trading signals — up to 10 per day",
            "🔍 AI Chart Analysis — 5 uploads per day",
            "📚 Full Trading Academy access",
            "🤖 AI Mentor — standard access",
        ],
    }
    feature_list  = features.get(plan.lower(), features["pro"])
    features_html = "".join(f"""
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:10px 8px;color:#374151;font-size:14px;">{f}</td>
  </tr>""" for f in feature_list)

    content = f"""
<h2 style="margin:0 0 8px;font-size:22px;color:#111827;font-weight:800;">
  Smart move, {first}. 💰
</h2>
<p style="color:#374151;line-height:1.7;margin:0 0 20px;font-size:15px;">
  While most traders are still guessing, you now have the same analytical tools
  used by professional desks — at a fraction of the cost.
  Your {plan_label} subscription is active.
</p>

<div style="background:linear-gradient(135deg,#667eea15,#764ba215);border:1px solid #667eea40;
            border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;">
  <p style="margin:0 0 4px;font-size:13px;color:#6b7280;">Your plan</p>
  <p style="margin:0 0 4px;font-size:22px;font-weight:800;color:#111827;">Gopipways {plan_label}</p>
  <p style="margin:0;font-size:14px;color:#667eea;font-weight:600;">{amount} / {billing_cycle}</p>
</div>

<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:14px 16px;margin-bottom:20px;">
  <p style="margin:0;font-size:13px;color:#92400e;line-height:1.6;">
    💡 <strong>One signal that hits TP on a standard lot covers your subscription cost many times over.</strong>
    Everything after that is profit.
  </p>
</div>

<p style="color:#374151;font-size:14px;margin:0 0 12px;font-weight:600;">What's unlocked in your plan:</p>
<table width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e5e7eb;border-radius:8px;margin-bottom:24px;">
  {features_html}
</table>

<div style="background:#f8fafc;border-radius:8px;padding:16px;margin-bottom:24px;border-left:4px solid #667eea;">
  <p style="margin:0;font-size:13px;color:#374151;font-weight:600;">Your first move as a Pro member:</p>
  <p style="margin:6px 0 0;font-size:13px;color:#6b7280;">
    Check today's live signals or upload a chart for instant AI analysis.
    Both tools are live and waiting.
  </p>
</div>

<div style="text-align:center;margin-bottom:20px;">
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);color:white;
            text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;">
    See Today's Live Signals →
  </a>
</div>

<p style="font-size:13px;color:#9ca3af;line-height:1.6;">
  Questions about your subscription? Reply to this email or contact
  <a href="mailto:contact@gopipways.com" style="color:#667eea;">contact@gopipways.com</a>
</p>"""
    return (f"Welcome to Gopipways {plan_label} — here's how to make it work 💰",
            _base(content, f"You just unlocked institutional tools most traders don't even know exist."))


def blog_published_email(full_name: str, post_title: str, post_excerpt: str,
                          post_slug: str, category: str = "Trading",
                          read_time: str = "5 min") -> tuple:
    first    = (full_name or "Trader").split()[0]
    post_url = f"{APP_BASE_URL}/blog/{post_slug}" if post_slug else f"{APP_BASE_URL}/dashboard.html"

    content = f"""
<p style="margin:0 0 16px;color:#374151;font-size:15px;line-height:1.7;">
  {first} — the article we just published might change how you read every chart
  from this point forward.
</p>

<div style="border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:24px;">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:8px 16px;">
    <span style="color:rgba(255,255,255,.9);font-size:12px;font-weight:600;text-transform:uppercase;
                 letter-spacing:.06em;">{category} &nbsp;·&nbsp; {read_time} read</span>
  </div>
  <div style="padding:24px;">
    <h2 style="margin:0 0 12px;font-size:20px;font-weight:800;color:#111827;line-height:1.3;">
      {post_title}
    </h2>
    <p style="margin:0 0 20px;color:#6b7280;font-size:14px;line-height:1.7;">
      {post_excerpt}
    </p>
    <a href="{post_url}"
       style="display:inline-block;background:#111827;color:white;text-decoration:none;
              padding:11px 22px;border-radius:7px;font-weight:700;font-size:14px;">
      Read the Full Article →
    </a>
  </div>
</div>

<p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
  You're receiving this because you subscribed to Gopipways updates.
</p>"""
    return (f"{post_title}",
            _base(content, f"New on Gopipways: {post_title} — {read_time} read. This one is worth your time."))


def password_reset_email(full_name: str, reset_url: str) -> tuple:
    """Sent when a user requests a password reset."""
    first = (full_name or "Trader").split()[0]
    content = f"""
<h2 style="margin:0 0 8px;font-size:22px;color:#111827;">Let's get you back in, {first} 🔐</h2>
<p style="color:#374151;line-height:1.7;margin:0 0 24px;font-size:15px;">
  No problem — it happens. Click the button below to set a new password
  and get straight back to your account.
</p>

<div style="text-align:center;margin:28px 0;">
  <a href="{reset_url}"
     style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);color:white;
            text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;">
    Reset My Password →
  </a>
  <p style="margin:12px 0 0;font-size:12px;color:#9ca3af;">
    This link works once and expires in <strong style="color:#374151;">1 hour</strong>.
  </p>
</div>

<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:20px;">
  <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.6;">
    🔒 <strong style="color:#374151;">Didn't request this?</strong><br>
    No action needed — your account is completely secure and nothing has changed.
    You can safely ignore this email.
  </p>
</div>

<p style="font-size:13px;color:#9ca3af;line-height:1.6;margin:0;">
  If the button above doesn't work, contact us at
  <a href="mailto:contact@gopipways.com" style="color:#667eea;">contact@gopipways.com</a>
  and we'll sort it out.
</p>"""
    return ("Reset your Gopipways password — link inside",
            _base(content, f"Let's get you back in, {first}. Your reset link expires in 1 hour."))


# ── Log helper ─────────────────────────────────────────────────────────────────

async def log_email(user_id: int, email_type: str, to_email: str, success: bool):
    try:
        await database.execute(
            "INSERT INTO email_logs (user_id, email_type, to_email, success, sent_at) "
            "VALUES (:uid, :t, :e, :ok, NOW())",
            {"uid": user_id, "t": email_type, "e": to_email, "ok": success},
        )
    except Exception:
        pass


# ── Background task helpers (called from other modules) ───────────────────────

async def send_welcome_email_task(user_id: int, email: str, full_name: str):
    subject, html = welcome_email(full_name)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "welcome", email, ok)


# Alias used by main.py import: `from .email_service import send_welcome`
async def send_welcome(user_id: int, email: str, full_name: str):
    """Thin alias for send_welcome_email_task — used by main.py lifespan."""
    await send_welcome_email_task(user_id, email, full_name)


async def send_lesson_complete_task(user_id: int, email: str, full_name: str,
                                     lesson_title: str, module_title: str,
                                     next_lesson: Optional[str] = None,
                                     lesson_number: int = 0,
                                     total_lessons: int = 0):
    subject, html = lesson_complete_email(full_name, lesson_title, module_title,
                                          next_lesson, lesson_number, total_lessons)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "lesson_complete", email, ok)


async def send_certificate_task(user_id: int, email: str, full_name: str,
                                 course_title: str, cert_number: str):
    subject, html = certificate_email(full_name, course_title, cert_number)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "certificate", email, ok)


async def send_subscription_task(user_id: int, email: str, full_name: str,
                                  plan: str, amount: str, billing_cycle: str = "monthly"):
    subject, html = subscription_email(full_name, plan, amount, billing_cycle)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "subscription", email, ok)


async def send_blog_published_task(subscribers: list, post_title: str, post_excerpt: str,
                                    post_slug: str, category: str = "Trading",
                                    read_time: str = "5 min"):
    """
    Broadcast a blog post to all opted-in subscribers.
    Call from blog.py after a post is published:
        await send_blog_published_task(subscribers, title, excerpt, slug)
    subscribers = list of {"user_id": int, "email": str, "full_name": str}
    """
    sent = 0
    for sub in subscribers:
        subject, html = blog_published_email(
            sub.get("full_name", "Trader"),
            post_title, post_excerpt, post_slug, category, read_time
        )
        ok = await send_email(sub["email"], subject, html)
        if ok:
            await log_email(sub.get("user_id", 0), "blog_published", sub["email"], True)
            sent += 1
        else:
            await log_email(sub.get("user_id", 0), "blog_published", sub["email"], False)
    print(f"[EMAIL] Blog '{post_title}' sent to {sent}/{len(subscribers)} subscribers", flush=True)
    return sent


async def send_signal_alert_task(user_id: int, email: str, full_name: str,
                                  symbol: str, direction: str, entry: float,
                                  sl: float, tp: float,
                                  confidence: int = 0, timeframe: str = "H1",
                                  rationale: str = ""):
    # B7 — check user preference before sending; signal_alerts=False by default
    try:
        row = await database.fetch_one(
            "SELECT preferences FROM user_email_preferences WHERE user_id = :uid",
            {"uid": user_id}
        )
        if row:
            prefs = json.loads(row["preferences"] or "{}")
            if not prefs.get("signal_alerts", False):
                return  # User has not opted in to signal alerts
    except Exception:
        pass  # If table missing or parse fails, proceed (fail open for signals)
    subject, html = new_signal_email(full_name, symbol, direction, entry, sl, tp,
                                     confidence=confidence, timeframe=timeframe,
                                     rationale=rationale)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "signal_alert", email, ok)


# ── API routes ─────────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """
    Public endpoint — request a password reset link.
    Always returns success even if email not found (prevents user enumeration).
    """
    email = body.email.lower().strip()

    # B5 — rate limit: max 3 reset requests per email per hour
    try:
        recent_count = await database.fetch_one(
            "SELECT COUNT(*) as cnt FROM password_reset_tokens "
            "WHERE email = :email AND created_at > NOW() - INTERVAL '1 hour'",
            {"email": email}
        )
        if recent_count and recent_count["cnt"] >= 3:
            return {"success": True, "message": "If that email is registered, a reset link has been sent."}
    except Exception:
        pass  # Table may not exist yet — proceed safely

    # Look up user — silently succeed if not found
    try:
        row = await database.fetch_one(
            "SELECT id, full_name FROM users WHERE LOWER(email) = :email AND is_active = TRUE",
            {"email": email}
        )
    except Exception as e:
        print(f"[EMAIL/RESET] DB error looking up user: {e}", flush=True)
        return {"success": True, "message": "If that email is registered, a reset link has been sent."}

    if row:
        user_id   = row["id"]
        full_name = row["full_name"] or "Trader"

        # Expire any existing unused tokens for this user
        try:
            await database.execute(
                "UPDATE password_reset_tokens SET used = TRUE "
                "WHERE user_id = :uid AND used = FALSE",
                {"uid": user_id}
            )
        except Exception:
            pass

        # Generate a secure token — 64 hex chars
        raw_token = secrets.token_urlsafe(48)
        expires   = datetime.utcnow() + timedelta(hours=1)

        try:
            await database.execute(
                "INSERT INTO password_reset_tokens "
                "(user_id, email, token, expires_at) VALUES (:uid, :email, :token, :exp)",
                {"uid": user_id, "email": email, "token": raw_token, "exp": expires}
            )
        except Exception as e:
            print(f"[EMAIL/RESET] Failed to store token: {e}", flush=True)
            return {"success": True, "message": "If that email is registered, a reset link has been sent."}

        # Build reset URL — links to the dashboard reset page with token in query string
        reset_url = f"{APP_BASE_URL}/dashboard.html?reset_token={raw_token}"

        # Send email
        subject, html = password_reset_email(full_name, reset_url)
        ok = await send_email(email, subject, html)
        await log_email(user_id, "password_reset", email, ok)

        print(f"[EMAIL/RESET] Reset link sent to {email} (user_id={user_id}, token={raw_token[:8]}...)", flush=True)

    return {"success": True, "message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    """
    Public endpoint — verify reset token and update password.
    Token is single-use and expires after 1 hour.
    """
    import bcrypt

    if not body.token or len(body.new_password) < 8:
        raise HTTPException(400, "Token is required and password must be at least 8 characters.")

    # Look up the token
    try:
        row = await database.fetch_one(
            "SELECT user_id, email, expires_at, used "
            "FROM password_reset_tokens WHERE token = :token",
            {"token": body.token}
        )
    except Exception as e:
        print(f"[EMAIL/RESET] DB error verifying token: {e}", flush=True)
        raise HTTPException(500, "Server error. Please try again.")

    if not row:
        raise HTTPException(400, "Invalid or expired reset link. Please request a new one.")

    if row["used"]:
        raise HTTPException(400, "This reset link has already been used. Please request a new one.")

    # B2 — strip timezone from DB timestamp before comparing with naive utcnow()
    expires_at = row["expires_at"]
    if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)
    if datetime.utcnow() > expires_at:
        raise HTTPException(400, "This reset link has expired (links are valid for 1 hour). Please request a new one.")

    # Hash the new password
    hashed = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()

    # B3 — update password; column verified as hashed_password from auth.py registration INSERT
    # If your auth.py uses a different column name, update here to match
    try:
        result = await database.execute(
            "UPDATE users SET hashed_password = :pw WHERE id = :uid",
            {"pw": hashed, "uid": row["user_id"]}
        )
    except Exception as e:
        # Column name mismatch guard — try alternate column names used by some FastAPI templates
        if "hashed_password" in str(e):
            try:
                await database.execute(
                    "UPDATE users SET password_hash = :pw WHERE id = :uid",
                    {"pw": hashed, "uid": row["user_id"]}
                )
            except Exception as e2:
                print(f"[EMAIL/RESET] Failed to update password (tried both column names): {e2}", flush=True)
                raise HTTPException(500, "Failed to update password. Please try again.")
        else:
            print(f"[EMAIL/RESET] Failed to update password: {e}", flush=True)
            raise HTTPException(500, "Failed to update password. Please try again.")

    # Mark token as used
    await database.execute(
        "UPDATE password_reset_tokens SET used = TRUE WHERE token = :token",
        {"token": body.token}
    )

    print(f"[EMAIL/RESET] Password reset successful for user_id={row['user_id']}", flush=True)
    return {"success": True, "message": "Password updated successfully. You can now log in."}


@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
    """
    Public endpoint — check if a reset token is valid before showing the reset form.
    Called by the frontend when user lands on the reset page.
    """
    if not token:
        raise HTTPException(400, "Token is required.")

    try:
        row = await database.fetch_one(
            "SELECT expires_at, used FROM password_reset_tokens WHERE token = :token",
            {"token": token}
        )
    except Exception:
        raise HTTPException(500, "Server error.")

    if not row or row["used"]:
        return {"valid": False, "message": "This reset link is invalid or has expired."}
    expires_at = row["expires_at"]
    if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)
    if datetime.utcnow() > expires_at:
        return {"valid": False, "message": "This reset link is invalid or has expired."}

    return {"valid": True, "message": "Token is valid. You may reset your password."}


class EmailCaptureRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = ""
    source: Optional[str] = "general"


class TestEmailRequest(BaseModel):
    to_email: EmailStr
    template: str = "welcome"


@router.post("/capture")
async def capture_email(body: EmailCaptureRequest):
    """Public endpoint — capture a lead email and send a welcome message."""
    try:
        await database.execute(
            "INSERT INTO email_subscribers (email, name, source, subscribed_at) "
            "VALUES (:e, :n, :s, NOW()) "
            "ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name, source=EXCLUDED.source",
            {"e": body.email, "n": body.name or "", "s": body.source},
        )
    except Exception as e:
        print(f"[EMAIL CAPTURE] {e}", flush=True)

    subject = "Welcome to Gopipways — Your free trading resources are ready"
    html = _base(f"""
<h2 style="margin:0 0 8px;font-size:22px;color:#111827;">You're in! 🎉</h2>
<p style="color:#374151;line-height:1.6;margin:0 0 20px;">
  Thanks for joining Gopipways. Your free account gives you access to:
</p>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:10px 8px;">📚 <strong>Trading Academy</strong> — SMC curriculum, quizzes and certificates</td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:10px 8px;">📊 <strong>Live Signals</strong> — Real institutional-grade trade setups</td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:10px 8px;">💰 <strong>Risk Calculator</strong> — Proper position sizing every time</td>
  </tr>
  <tr>
    <td style="padding:10px 8px;">🤖 <strong>AI Mentor</strong> — SMC trading questions answered instantly</td>
  </tr>
</table>
<div style="text-align:center;margin-bottom:20px;">
  <a href="{APP_BASE_URL}/dashboard.html"
     style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);color:white;
            text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;">
    Explore Gopipways →
  </a>
</div>
<p style="font-size:13px;color:#9ca3af;text-align:center;">
  Questions? Reply to this email — we read every one.
</p>""",
    "Your Gopipways account is ready — signals, academy, AI and more.")
    ok = await send_email(body.email, subject, html)
    await log_email(0, "capture", body.email, ok)  # B12 — log lead capture emails
    return {"success": True, "message": "Check your email!"}


@router.get("/preferences")
async def get_email_preferences(current_user=Depends(get_current_user)):
    user_id = get_user_id(current_user)
    defaults = {"welcome": True, "lesson_complete": True, "certificate": True,
                "signal_alerts": False, "weekly_digest": False, "promotions": False}
    try:
        row = await database.fetch_one(
            "SELECT preferences FROM user_email_preferences WHERE user_id = :uid", {"uid": user_id}
        )
        if row:
            return {**defaults, **json.loads(row["preferences"])}
    except Exception:
        pass
    return defaults


@router.post("/preferences")
async def update_email_preferences(preferences: dict, current_user=Depends(get_current_user)):
    user_id = get_user_id(current_user)
    try:
        await database.execute(
            "INSERT INTO user_email_preferences (user_id, preferences, updated_at) "
            "VALUES (:uid, :p, NOW()) "
            "ON CONFLICT (user_id) DO UPDATE SET preferences=EXCLUDED.preferences, updated_at=NOW()",
            {"uid": user_id, "p": json.dumps(preferences)},
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/send-test")
async def send_test_email(body: TestEmailRequest, current_user=Depends(get_current_user)):
    """Admin only — verify email configuration."""
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin only")
    templates = {
        "welcome":          lambda: welcome_email("Test User"),
        "lesson_complete":  lambda: lesson_complete_email("Test User", "Introduction to SMC", "Beginner Module", "Order Blocks & Fair Value Gaps"),
        "certificate":      lambda: certificate_email("Test User", "Advanced SMC Trading", "GP-2026-001"),
        "signal":           lambda: new_signal_email("Test User", "XAUUSD", "BUY", 4525.0, 4450.0, 4650.0, confidence=85, timeframe="H1", rationale="Bullish BOS confirmed at 4600 with OB at 4525 in discount zone after liquidity sweep."),
        "subscription":     lambda: subscription_email("Test User", "Pro", "₦15,000", "monthly"),
        "blog":             lambda: blog_published_email("Test User", "How Smart Money Concepts Can Transform Your Trading", "Most retail traders lose because they trade against institutions. In this article, we break down exactly how to read institutional footprints using SMC — order blocks, fair value gaps and liquidity sweeps.", "how-smc-transforms-trading", "SMC Education", "6 min"),
        "password_reset":   lambda: password_reset_email("Test User", f"{APP_BASE_URL}/dashboard.html?reset_token=TEST_TOKEN_EXAMPLE"),
    }
    fn = templates.get(body.template)
    if not fn:
        raise HTTPException(400, f"Unknown template. Options: {list(templates.keys())}")
    subject, html = fn()
    ok = await send_email(body.to_email, subject, html)
    return {"success": ok, "template": body.template, "to": body.to_email}


@router.post("/broadcast")
async def broadcast_email(payload: dict, background_tasks: BackgroundTasks,
                           current_user=Depends(get_current_user)):
    """
    Admin only — send a personalised bulk email to all users or a tier subset.

    Payload:
      subject    : str  — email subject line
      html_body  : str  — main content (use {{first_name}} for personalisation)
      filter     : str  — "all" | "pro" | "free" | "basic" (default: "all")
      preview    : bool — if true, returns user count without sending (dry run)
    """
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin only")

    subject   = payload.get("subject", "Message from Gopipways")
    html_body = payload.get("html_body", "")
    tier      = payload.get("filter", "all")
    dry_run   = payload.get("preview", False)

    if not html_body:
        raise HTTPException(400, "html_body is required")

    sql    = "SELECT id, email, full_name FROM users WHERE is_active = TRUE"
    params = {}
    if tier != "all":
        sql += " AND subscription_tier = :tier"
        params["tier"] = tier

    # Dry run — return recipient count without sending
    if dry_run:
        rows = await database.fetch_all(sql, params)
        return {
            "status":     "preview",
            "recipients": len(rows),
            "filter":     tier,
            "subject":    subject,
            "message":    f"Ready to send to {len(rows)} users. Set preview=false to send."
        }

    async def _send_all():
        rows = await database.fetch_all(sql, params)
        sent = failed = 0
        print(f"[EMAIL BROADCAST] Starting — {len(rows)} recipients, filter={tier}", flush=True)

        for row in rows:
            # Personalise — replace {{first_name}} in html_body with user's first name
            first_name = (row["full_name"] or "Trader").split()[0]
            user_id    = row["id"]

            # Build personalised greeting block
            greeting = f"""
<p style="margin:0 0 20px;color:#374151;font-size:15px;">
  Hi <strong>{first_name}</strong>,
</p>"""

            # Build unsubscribe link — links to dashboard email preferences
            unsubscribe = f"""
<div style="text-align:center;margin-top:24px;padding-top:16px;border-top:1px solid #e5e7eb;">
  <p style="margin:0;font-size:12px;color:#9ca3af;">
    You're receiving this as a registered Gopipways user.<br>
    <a href="{APP_BASE_URL}/dashboard.html" style="color:#6b7280;">
      Manage email preferences
    </a>
  </p>
</div>"""

            # Inject first_name into the html_body if placeholder used
            personalised_body = html_body.replace("{{first_name}}", first_name)

            full_html = _base(greeting + personalised_body + unsubscribe)

            ok = await send_email(row["email"], subject, full_html)
            if ok:
                sent += 1
                await log_email(user_id, "broadcast", row["email"], True)
            else:
                failed += 1
                await log_email(user_id, "broadcast", row["email"], False)
            await asyncio.sleep(0.1)  # B8 — 10/sec max to stay within Brevo rate limits

        print(f"[EMAIL BROADCAST] ✅ Complete — {sent} sent, {failed} failed out of {len(rows)}", flush=True)

    background_tasks.add_task(_send_all)
    return {"status": "queued", "filter": tier,
            "message": "Broadcast started in background. Check Railway logs for progress."}
