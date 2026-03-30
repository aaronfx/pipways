"""
Email Service for Gopipways
Handles: welcome emails, lesson completion, signal alerts, weekly digest

Provider: SpaceMail SMTP (contact@gopipways.com)
  Uses port 587 (STARTTLS) or port 465 (SSL) — auto-detected from SMTP_PORT.

Environment variables:
  EMAIL_PROVIDER        — "smtp" (SpaceMail uses SMTP)
  SMTP_HOST             — smtp.spacemail.com
  SMTP_PORT             — 587 (STARTTLS) or 465 (SSL)
  SMTP_USER             — contact@gopipways.com
  SMTP_PASSWORD         — your SpaceMail password
  EMAIL_FROM_NAME       — "Gopipways" (default)
  EMAIL_FROM_ADDRESS    — contact@gopipways.com
  APP_BASE_URL          — https://www.gopipways.com
"""

import os
import re
import hmac
import httpx
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr

from .database import database
from .security import get_current_user, get_user_id, is_admin_user

router = APIRouter()

EMAIL_PROVIDER  = os.getenv("EMAIL_PROVIDER", "smtp")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN  = os.getenv("MAILGUN_DOMAIN", "")
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.spacemail.com")
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
        if EMAIL_PROVIDER == "mailgun" and MAILGUN_API_KEY and MAILGUN_DOMAIN:
            return await _send_mailgun(to_email, from_field, subject, html_body, text_body)
        elif SMTP_USER and SMTP_PASSWORD:
            return await _send_smtp(to_email, from_field, subject, html_body, text_body)
        else:
            print(f"[EMAIL] No provider configured — skipping email to {to_email}", flush=True)
            return False
    except Exception as e:
        print(f"[EMAIL] Send failed to {to_email}: {e}", flush=True)
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
        if SMTP_PORT == 465:
            # SSL connection — SpaceMail port 465
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
                s.login(SMTP_USER, SMTP_PASSWORD)
                s.sendmail(FROM_ADDRESS, [to], msg.as_string())
        else:
            # STARTTLS connection — SpaceMail port 587 (default)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(SMTP_USER, SMTP_PASSWORD)
                s.sendmail(FROM_ADDRESS, [to], msg.as_string())
        return True
    return await asyncio.get_event_loop().run_in_executor(None, _sync)


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
    <a href="{APP_BASE_URL}/settings" style="color:#6b7280;">Manage email preferences</a>
  </p>
</td></tr>
</table></td></tr></table></body></html>"""


# ── Templates ──────────────────────────────────────────────────────────────────

def welcome_email(full_name: str) -> tuple:
    first = (full_name or "Trader").split()[0]
    content = f"""
<h2 style="margin:0 0 16px;font-size:22px;color:#111827;">Welcome to Gopipways, {first}! 🎉</h2>
<p style="color:#374151;line-height:1.6;margin:0 0 20px;">Your account is ready. Here's what you have for free:</p>
<table width="100%" cellpadding="10" cellspacing="0" style="margin-bottom:24px;">
  <tr style="border-bottom:1px solid #f3f4f6;"><td>📚 <strong>Trading Academy</strong> — Full curriculum, quizzes & certificates. 100% free.</td></tr>
  <tr style="border-bottom:1px solid #f3f4f6;"><td>💰 <strong>Risk Calculator</strong> — Position sizing before every trade.</td></tr>
  <tr style="border-bottom:1px solid #f3f4f6;"><td>📊 <strong>Trading Signals</strong> — Active signals from our analysts.</td></tr>
  <tr><td>🤖 <strong>AI Mentor</strong> — Ask anything about forex trading.</td></tr>
</table>
<a href="{APP_BASE_URL}/dashboard.html" style="display:inline-block;background:#3b82f6;color:white;
   text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;">
   Start Learning Now →
</a>
<p style="margin:24px 0 0;font-size:13px;color:#9ca3af;">Questions? Just reply to this email.</p>"""
    return ("Welcome to Gopipways — Your Trading Journey Starts Now",
            _base(content, f"Welcome {first}! Your free account is ready."))


def lesson_complete_email(full_name: str, lesson_title: str, module_title: str,
                           next_lesson: Optional[str] = None) -> tuple:
    first = (full_name or "Trader").split()[0]
    next_block = f"""
<div style="background:#eff6ff;border-radius:8px;padding:16px;margin:20px 0;">
  <p style="margin:0;font-size:14px;color:#1e40af;"><strong>Up next:</strong> {next_lesson}</p>
  <a href="{APP_BASE_URL}/academy.html" style="display:inline-block;margin-top:10px;background:#3b82f6;
     color:white;text-decoration:none;padding:10px 20px;border-radius:6px;font-size:14px;font-weight:600;">
     Continue Learning →
  </a>
</div>""" if next_lesson else ""

    content = f"""
<h2 style="margin:0 0 8px;font-size:22px;color:#111827;">Lesson Complete! ✅</h2>
<p style="color:#374151;margin:0 0 20px;">
  Great work, {first}. You finished <strong>"{lesson_title}"</strong> in <em>{module_title}</em>.
</p>{next_block}
<p style="font-size:13px;color:#9ca3af;margin:16px 0 0;">Keep going — consistency is the edge.</p>"""
    return (f"✅ You completed: {lesson_title}",
            _base(content, f"Great work! You finished {lesson_title}."))


def certificate_email(full_name: str, course_title: str, cert_number: str) -> tuple:
    first = (full_name or "Trader").split()[0]
    content = f"""
<div style="text-align:center;margin-bottom:24px;">
  <div style="font-size:56px;">🏆</div>
  <h2 style="margin:12px 0 8px;font-size:24px;color:#111827;">Certificate Earned!</h2>
  <p style="color:#374151;margin:0;">Congratulations {first} — you completed <strong>{course_title}</strong>.</p>
</div>
<div style="background:#fefce8;border:1px solid #fde68a;border-radius:10px;padding:20px;text-align:center;margin-bottom:24px;">
  <p style="margin:0;font-size:13px;color:#92400e;">Certificate #{cert_number}</p>
</div>
<a href="{APP_BASE_URL}/academy.html" style="display:inline-block;background:#3b82f6;color:white;
   text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;">
   View Certificate →
</a>"""
    return (f"🏆 Certificate Earned: {course_title}",
            _base(content, f"You earned a certificate for {course_title}!"))


def new_signal_email(full_name: str, symbol: str, direction: str,
                     entry: float, sl: float, tp: float) -> tuple:
    first  = (full_name or "Trader").split()[0]
    color  = "#22c55e" if direction.upper() == "BUY" else "#ef4444"
    rr     = round(abs(tp - entry) / abs(entry - sl), 2) if abs(entry - sl) > 0 else 0
    table_rows = f"""
<tr style="background:#f9fafb;"><td style="padding:10px;font-weight:600;">Direction</td>
  <td style="padding:10px;color:{color};font-weight:700;">{direction.upper()}</td></tr>
<tr><td style="padding:10px;font-weight:600;">Entry</td><td style="padding:10px;">{entry}</td></tr>
<tr style="background:#f9fafb;"><td style="padding:10px;font-weight:600;">Stop Loss</td>
  <td style="padding:10px;color:#ef4444;">{sl}</td></tr>
<tr><td style="padding:10px;font-weight:600;">Take Profit</td>
  <td style="padding:10px;color:#22c55e;">{tp}</td></tr>
<tr style="background:#f9fafb;"><td style="padding:10px;font-weight:600;">R:R Ratio</td>
  <td style="padding:10px;">1:{rr}</td></tr>"""
    content = f"""
<h2 style="margin:0 0 16px;font-size:22px;color:#111827;">New Signal: {symbol} 📊</h2>
<p style="color:#374151;margin:0 0 20px;">Hey {first}, a new {direction.upper()} signal is live for {symbol}.</p>
<table width="100%" cellpadding="0" cellspacing="0"
       style="border:1px solid #e5e7eb;border-radius:8px;margin-bottom:20px;">{table_rows}</table>
<a href="{APP_BASE_URL}/dashboard.html#/signals" style="display:inline-block;background:{color};
   color:white;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;">
   View Full Analysis →
</a>
<p style="margin:16px 0 0;font-size:12px;color:#9ca3af;">This is not financial advice. Always use proper risk management.</p>"""
    return (f"📊 New Signal: {symbol} {direction.upper()}",
            _base(content, f"New {direction} signal for {symbol}"))


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
                                     next_lesson: Optional[str] = None):
    subject, html = lesson_complete_email(full_name, lesson_title, module_title, next_lesson)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "lesson_complete", email, ok)


async def send_certificate_task(user_id: int, email: str, full_name: str,
                                 course_title: str, cert_number: str):
    subject, html = certificate_email(full_name, course_title, cert_number)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "certificate", email, ok)


async def send_signal_alert_task(user_id: int, email: str, full_name: str,
                                  symbol: str, direction: str, entry: float,
                                  sl: float, tp: float):
    subject, html = new_signal_email(full_name, symbol, direction, entry, sl, tp)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "signal_alert", email, ok)


# ── API routes ─────────────────────────────────────────────────────────────────

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

    subject = "Welcome to Gopipways — Your free trading resources"
    html = _base(f"""
<h2 style="margin:0 0 16px;color:#111827;">Thanks for joining! 👋</h2>
<p style="color:#374151;line-height:1.6;">
  You now have access to our free <strong>Trading Academy</strong> and <strong>Risk Calculator</strong>.
  No credit card needed.
</p>
<a href="{APP_BASE_URL}" style="display:inline-block;margin-top:16px;background:#3b82f6;color:white;
   text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:700;">Explore Gopipways →</a>""",
    "Your free trading resources are ready!")
    await send_email(body.email, subject, html)
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
            import json
            return {**defaults, **json.loads(row["preferences"])}
    except Exception:
        pass
    return defaults


@router.post("/preferences")
async def update_email_preferences(preferences: dict, current_user=Depends(get_current_user)):
    import json
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
        "lesson_complete":  lambda: lesson_complete_email("Test User", "Introduction to Forex", "Beginner Module", "Support & Resistance"),
        "certificate":      lambda: certificate_email("Test User", "Advanced SMC Trading", "PW-TEST-001"),
        "signal":           lambda: new_signal_email("Test User", "EURUSD", "BUY", 1.0850, 1.0800, 1.0950),
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
    """Admin only — email all users or a tier subset."""
    if not is_admin_user(current_user):
        raise HTTPException(403, "Admin only")
    subject   = payload.get("subject", "Message from Gopipways")
    html_body = payload.get("html_body", "")
    tier      = payload.get("filter", "all")
    if not html_body:
        raise HTTPException(400, "html_body is required")

    sql    = "SELECT id, email, full_name FROM users WHERE is_active = TRUE"
    params = {}
    if tier != "all":
        sql += " AND subscription_tier = :tier"
        params["tier"] = tier

    async def _send_all():
        rows = await database.fetch_all(sql, params)
        sent = 0
        for row in rows:
            ok = await send_email(row["email"], subject, _base(html_body))
            if ok:
                sent += 1
        print(f"[EMAIL BROADCAST] {sent}/{len(rows)} sent", flush=True)

    background_tasks.add_task(_send_all)
    return {"status": "queued", "filter": tier}
