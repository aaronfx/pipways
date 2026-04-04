"""
Email Service for Gopipways
Handles: welcome emails, lesson completion, signal alerts, weekly digest,
         webinar confirmations and scheduled reminders (24h + 1h)

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

DASHBOARD_URL   = "https://www.gopipways.com/dashboard"


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
        # ── Webinar reminder columns (idempotent) ────────────────────────────
        "ALTER TABLE webinar_registrations ADD COLUMN IF NOT EXISTS reminded_at_24h TIMESTAMPTZ",
        "ALTER TABLE webinar_registrations ADD COLUMN IF NOT EXISTS reminded_at_1h  TIMESTAMPTZ",
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

        print(f"[EMAIL/Brevo] ❌ HTTP {res.status_code}: {res.text}", flush=True)

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
            timeout=20.0
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
    <a href="{DASHBOARD_URL}" style="color:#6b7280;">Manage email preferences</a>
  </p>
</td></tr>
</table></td></tr></table></body></html>"""


# ── Webinar date/calendar helpers ──────────────────────────────────────────────

def _fmt_session_date(scheduled_at) -> str:
    """Format a datetime object into a readable WAT string.
    Returns 'Date to be confirmed' gracefully for None/null values."""
    if scheduled_at is None or str(scheduled_at).strip().lower() in ("none", "", "null"):
        return "Date to be confirmed"
    try:
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
        # WAT = UTC+1
        wat = scheduled_at + timedelta(hours=1) if scheduled_at.tzinfo else scheduled_at
        return wat.strftime("%A, %d %B %Y at %I:%M %p WAT")
    except Exception:
        return "Date to be confirmed"


def _google_calendar_link(session_title: str, scheduled_at, duration_minutes: int = 60) -> str:
    """Build a Google Calendar 'Add to Calendar' URL from the session datetime.
    Returns an empty string if scheduled_at is missing or unparseable."""
    if scheduled_at is None or str(scheduled_at).strip().lower() in ("none", "", "null"):
        return ""
    try:
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
        # Work in UTC for the calendar link
        if hasattr(scheduled_at, "tzinfo") and scheduled_at.tzinfo:
            start_utc = scheduled_at.replace(tzinfo=None)
        else:
            start_utc = scheduled_at
        end_utc = start_utc + timedelta(minutes=duration_minutes)
        fmt = "%Y%m%dT%H%M%SZ"
        from urllib.parse import quote
        title_enc   = quote(session_title)
        details_enc = quote(f"Join on Gopipways: {DASHBOARD_URL}")
        location_enc = quote(DASHBOARD_URL)
        return (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={title_enc}"
            f"&dates={start_utc.strftime(fmt)}/{end_utc.strftime(fmt)}"
            f"&details={details_enc}"
            f"&location={location_enc}"
        )
    except Exception:
        return ""


# ── Webinar email templates ────────────────────────────────────────────────────

def webinar_confirmation_email(full_name: str, session_title: str,
                                presenter: str, scheduled_at,
                                duration_minutes: int = 60) -> tuple:
    first      = (full_name or "Trader").split()[0]
    date_str   = _fmt_session_date(scheduled_at)
    pres_line  = f"Host: {presenter}" if presenter and presenter != "TBA" else ""
    cal_url    = _google_calendar_link(session_title, scheduled_at, duration_minutes)

    cal_block = f"""
<div style="text-align:center;margin-bottom:20px;">
    <a href="{cal_url}"
       target="_blank"
       style="display:inline-block;color:#667eea;font-size:13px;font-weight:600;
              text-decoration:none;border:1px solid rgba(102,126,234,.3);
              padding:9px 22px;border-radius:7px;
              background:rgba(102,126,234,.07);">
        📅 Add to Google Calendar →
    </a>
</div>""" if cal_url else ""

    content = f"""
<h2 style="margin:0 0 8px;font-size:22px;color:#111827;">You're registered, {first}. ✅</h2>
<p style="color:#374151;line-height:1.7;margin:0 0 24px;font-size:15px;">
    Your spot is confirmed for the upcoming Gopipways live session.
</p>

<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;
            padding:24px;margin-bottom:24px;border-left:4px solid #667eea;">
    <p style="margin:0 0 6px;font-size:12px;color:#9ca3af;text-transform:uppercase;
              letter-spacing:.06em;">Session Details</p>
    <p style="margin:0 0 8px;font-size:19px;font-weight:800;color:#111827;">{session_title}</p>
    <p style="margin:0 0 4px;font-size:14px;color:#374151;">📅 {date_str}</p>
    {f'<p style="margin:0 0 4px;font-size:14px;color:#374151;">👤 {pres_line}</p>' if pres_line else ''}
    <p style="margin:0;font-size:14px;color:#374151;">⏱ {duration_minutes} minutes</p>
</div>

<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
            padding:16px;margin-bottom:24px;">
    <p style="margin:0;font-size:14px;color:#166534;line-height:1.6;">
        <strong>How to join:</strong><br>
        On session day, log in to your Gopipways dashboard and go to the
        Webinars section. Your session will be live and ready to watch
        inside the app — no Zoom link needed.
    </p>
</div>

<div style="text-align:center;margin-bottom:20px;">
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:14px 32px;border-radius:8px;
              font-weight:700;font-size:15px;">
        Go to Dashboard →
    </a>
</div>

{cal_block}

<p style="margin:0 0 16px;font-size:13px;color:#9ca3af;line-height:1.6;
          text-align:center;font-style:italic;">
    Check your email for confirmation.
    Return here on session day to watch live.
</p>

<p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.6;">
    You will receive a reminder 24 hours before and again 1 hour before
    the session starts.<br><br>
    Questions? Reply to this email — we read every one.
</p>"""

    return (
        f"You're registered — {session_title}",
        _base(content, f"{first}, your spot is confirmed. We'll remind you before it starts.")
    )


def webinar_reminder_email(full_name: str, session_title: str,
                            presenter: str, scheduled_at,
                            duration_minutes: int = 60,
                            reminder_type: str = "24h") -> tuple:
    """
    reminder_type: "24h" or "1h"
    """
    first    = (full_name or "Trader").split()[0]
    date_str = _fmt_session_date(scheduled_at)
    pres_line = f"👤 {presenter}" if presenter and presenter != "TBA" else ""

    if reminder_type == "1h":
        urgency_heading = f"Starting in 1 hour — {session_title}"
        urgency_sub     = "Your Gopipways live session starts in <strong>1 hour</strong>. Time to get ready."
        time_note       = f"<p style=\"margin:0 0 4px;font-size:14px;color:#374151;\">🕐 Today at {_fmt_session_date(scheduled_at).split('at')[-1].strip()}</p>"
        reminder_note   = ""
        subject         = f"Starting in 1 hour — {session_title}"
        preview         = f"Your session starts in 1 hour, {first}. Log in to Gopipways now."
        cta_label       = "Join Now →"
    else:
        urgency_heading = f"Tomorrow — {session_title}"
        urgency_sub     = "Your Gopipways live session is <strong>tomorrow</strong>. Here are your details."
        time_note       = f"<p style=\"margin:0 0 4px;font-size:14px;color:#374151;\">📅 {date_str}</p>"
        reminder_note   = """<p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.6;">
            You will receive one more reminder 1 hour before it starts.
        </p>"""
        subject         = f"Tomorrow — {session_title} | Gopipways"
        preview         = f"Your session is tomorrow, {first}. Here's everything you need."
        cta_label       = "Go to Dashboard →"

    content = f"""
<h2 style="margin:0 0 8px;font-size:22px;color:#111827;">{urgency_heading} 🔔</h2>
<p style="color:#374151;line-height:1.7;margin:0 0 24px;font-size:15px;">
    Hi {first}, {urgency_sub}
</p>

<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;
            padding:24px;margin-bottom:24px;border-left:4px solid #667eea;">
    <p style="margin:0 0 6px;font-size:12px;color:#9ca3af;text-transform:uppercase;
              letter-spacing:.06em;">Your Session</p>
    <p style="margin:0 0 8px;font-size:19px;font-weight:800;color:#111827;">{session_title}</p>
    {time_note}
    {f'<p style="margin:0 0 4px;font-size:14px;color:#374151;">{pres_line}</p>' if pres_line else ''}
    <p style="margin:0;font-size:14px;color:#374151;">⏱ {duration_minutes} minutes</p>
</div>

<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
            padding:16px;margin-bottom:24px;">
    <p style="margin:0;font-size:14px;color:#92400e;line-height:1.6;">
        <strong>How to join:</strong><br>
        Log in to your Gopipways dashboard and go to the Webinars section.
        Click <strong>Join Session</strong> when it goes live.
        No Zoom link needed — everything is inside the app.
    </p>
</div>

<div style="text-align:center;margin-bottom:24px;">
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:14px 32px;border-radius:8px;
              font-weight:700;font-size:15px;">
        {cta_label}
    </a>
    <p style="margin:8px 0 0;font-size:12px;color:#9ca3af;">
        www.gopipways.com/dashboard
    </p>
</div>

{reminder_note}"""

    return (subject, _base(content, preview))


# ── Webinar reminder scheduler ─────────────────────────────────────────────────

async def _run_webinar_reminders():
    """
    Runs every hour via APScheduler.
    Checks for sessions starting in ~24h or ~1h and emails unreminded registrants.
    Marks reminded_at_24h / reminded_at_1h to prevent double-sends.
    """
    now = datetime.utcnow()

    # ── 24-hour window: sessions starting between 23h and 25h from now ──────
    window_24h_start = now + timedelta(hours=23)
    window_24h_end   = now + timedelta(hours=25)

    # ── 1-hour window: sessions starting between 50min and 70min from now ───
    window_1h_start  = now + timedelta(minutes=50)
    window_1h_end    = now + timedelta(minutes=70)

    try:
        # ── Send 24h reminders ───────────────────────────────────────────────
        rows_24h = await database.fetch_all(
            """
            SELECT wr.id AS reg_id, wr.user_id,
                   u.email, u.full_name,
                   w.id AS webinar_id, w.title, w.presenter,
                   w.scheduled_at, w.duration_minutes
            FROM webinar_registrations wr
            JOIN users u ON u.id = wr.user_id
            JOIN webinars w ON w.id = wr.webinar_id
            WHERE w.scheduled_at BETWEEN :start AND :end
              AND wr.reminded_at_24h IS NULL
              AND u.is_active = TRUE
            """,
            {"start": window_24h_start, "end": window_24h_end}
        )

        sent_24h = 0
        for row in rows_24h:
            subject, html = webinar_reminder_email(
                full_name       = row["full_name"] or "Trader",
                session_title   = row["title"],
                presenter       = row["presenter"] or "",
                scheduled_at    = row["scheduled_at"],
                duration_minutes= row["duration_minutes"] or 60,
                reminder_type   = "24h",
            )
            ok = await send_email(row["email"], subject, html)
            if ok:
                sent_24h += 1
                await log_email(row["user_id"], "webinar_reminder_24h", row["email"], True)
            else:
                await log_email(row["user_id"], "webinar_reminder_24h", row["email"], False)

            # Mark regardless of send success to avoid retry spam
            await database.execute(
                "UPDATE webinar_registrations SET reminded_at_24h = :now WHERE id = :id",
                {"now": now, "id": row["reg_id"]}
            )
            await asyncio.sleep(0.1)

        if sent_24h:
            print(f"[WEBINAR REMINDERS] 24h — sent {sent_24h} reminder(s)", flush=True)

        # ── Send 1h reminders ────────────────────────────────────────────────
        rows_1h = await database.fetch_all(
            """
            SELECT wr.id AS reg_id, wr.user_id,
                   u.email, u.full_name,
                   w.id AS webinar_id, w.title, w.presenter,
                   w.scheduled_at, w.duration_minutes
            FROM webinar_registrations wr
            JOIN users u ON u.id = wr.user_id
            JOIN webinars w ON w.id = wr.webinar_id
            WHERE w.scheduled_at BETWEEN :start AND :end
              AND wr.reminded_at_1h IS NULL
              AND u.is_active = TRUE
            """,
            {"start": window_1h_start, "end": window_1h_end}
        )

        sent_1h = 0
        for row in rows_1h:
            subject, html = webinar_reminder_email(
                full_name       = row["full_name"] or "Trader",
                session_title   = row["title"],
                presenter       = row["presenter"] or "",
                scheduled_at    = row["scheduled_at"],
                duration_minutes= row["duration_minutes"] or 60,
                reminder_type   = "1h",
            )
            ok = await send_email(row["email"], subject, html)
            if ok:
                sent_1h += 1
                await log_email(row["user_id"], "webinar_reminder_1h", row["email"], True)
            else:
                await log_email(row["user_id"], "webinar_reminder_1h", row["email"], False)

            await database.execute(
                "UPDATE webinar_registrations SET reminded_at_1h = :now WHERE id = :id",
                {"now": now, "id": row["reg_id"]}
            )
            await asyncio.sleep(0.1)

        if sent_1h:
            print(f"[WEBINAR REMINDERS] 1h — sent {sent_1h} reminder(s)", flush=True)

    except Exception as e:
        print(f"[WEBINAR REMINDERS] ❌ Scheduler error: {e}", flush=True)


def start_webinar_reminder_scheduler():
    """
    Start the APScheduler job that fires every hour to send webinar reminders.
    Call this from main.py lifespan after DB is initialised:

        from backend.email_service import start_webinar_reminder_scheduler
        start_webinar_reminder_scheduler()
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _run_webinar_reminders,
            trigger="interval",
            hours=1,
            id="webinar_reminders",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            _run_reengagement_emails,
            trigger="interval",
            hours=24,
            id="reengagement_emails",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
        print("[WEBINAR REMINDERS] ✅ Scheduler started — checking every hour", flush=True)
        print("[RE-ENGAGEMENT] ✅ Scheduler started — checking daily", flush=True)
        return scheduler
    except ImportError:
        print("[WEBINAR REMINDERS] ⚠️  APScheduler not installed. Run: pip install apscheduler", flush=True)
        return None
    except Exception as e:
        print(f"[WEBINAR REMINDERS] ❌ Failed to start scheduler: {e}", flush=True)
        return None


# ── Webinar task helpers ───────────────────────────────────────────────────────

async def send_webinar_confirmation_task(user_id: int, email: str, full_name: str,
                                          session_title: str, presenter: str,
                                          scheduled_at, duration_minutes: int = 60,
                                          webinar_id: Optional[int] = None):
    """
    Send registration confirmation immediately after user registers.
    Called from webinars.py register endpoint.

    If scheduled_at arrives as None (caller didn't pass it), we fetch the full
    webinar row from the DB using webinar_id so the email always has a real date.
    """
    _missing = scheduled_at is None or str(scheduled_at).strip().lower() in ("none", "", "null")

    if _missing and webinar_id:
        try:
            row = await database.fetch_one(
                "SELECT scheduled_at, duration_minutes, presenter, title "
                "FROM webinars WHERE id = :id",
                {"id": webinar_id}
            )
            if row:
                scheduled_at   = row["scheduled_at"]
                duration_minutes = row["duration_minutes"] or duration_minutes
                if not presenter or presenter in ("", "TBA"):
                    presenter = row["presenter"] or ""
                if not session_title:
                    session_title = row["title"] or session_title
                print(f"[WEBINAR EMAIL] Fetched scheduled_at={scheduled_at} for webinar_id={webinar_id}", flush=True)
        except Exception as e:
            print(f"[WEBINAR EMAIL] ⚠️  Could not fetch webinar row: {e}", flush=True)
    elif _missing:
        print(f"[WEBINAR EMAIL] ⚠️  scheduled_at is None and no webinar_id provided — date will show as 'Date to be confirmed'", flush=True)

    subject, html = webinar_confirmation_email(
        full_name        = full_name,
        session_title    = session_title,
        presenter        = presenter,
        scheduled_at     = scheduled_at,
        duration_minutes = duration_minutes,
    )
    ok = await send_email(email, subject, html)
    await log_email(user_id, "webinar_confirmation", email, ok)
    print(f"[WEBINAR EMAIL] Confirmation {'✅' if ok else '❌'} → {email} ({session_title})", flush=True)



# ── Re-engagement email + scheduler ───────────────────────────────────────────

def reengagement_email(full_name: str) -> tuple:
    """
    Sent to users who registered 7 days ago but have not returned to the platform.
    Tone: warm, value-focused, no guilt. Creates FOMO around live activity.
    """
    first = (full_name or "Trader").split()[0]
    content = f"""
<h2 style="margin:0 0 10px;font-size:22px;color:#111827;font-weight:800;line-height:1.3;">
    {first}, the market has moved since you joined.
</h2>

<p style="color:#374151;line-height:1.75;margin:0 0 16px;font-size:15px;">
    A week ago you joined Gopipways. Since then, our traders have received live
    signals, attended mentorship sessions, and used AI chart analysis on real setups
    that moved exactly as the analysis predicted.
</p>

<p style="color:#374151;line-height:1.75;margin:0 0 22px;font-size:15px;">
    You have access to all of it. We just want to make sure you know what's waiting.
</p>

<div style="background:#111827;border-radius:10px;padding:18px 20px;margin-bottom:22px;">
    <p style="margin:0 0 12px;font-size:12px;color:#9ca3af;text-transform:uppercase;
              letter-spacing:.07em;font-weight:600;">What's active on your dashboard right now</p>
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:8px 0;border-bottom:1px solid #1f2937;">
                <span style="color:#fbbf24;font-size:13px;font-weight:600;">📊 Live Signals</span>
                <span style="color:#6b7280;font-size:13px;margin-left:8px;">
                    Active trade setups with full entry and exit levels
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding:8px 0;border-bottom:1px solid #1f2937;">
                <span style="color:#34d399;font-size:13px;font-weight:600;">🎓 Mentorship Sessions</span>
                <span style="color:#6b7280;font-size:13px;margin-left:8px;">
                    Upcoming live sessions — register before they fill up
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding:8px 0;border-bottom:1px solid #1f2937;">
                <span style="color:#60a5fa;font-size:13px;font-weight:600;">🔍 AI Chart Analysis</span>
                <span style="color:#6b7280;font-size:13px;margin-left:8px;">
                    Upload any chart — get professional-level analysis in seconds
                </span>
            </td>
        </tr>
        <tr>
            <td style="padding:8px 0;">
                <span style="color:#a78bfa;font-size:13px;font-weight:600;">📚 Trading Academy</span>
                <span style="color:#6b7280;font-size:13px;margin-left:8px;">
                    Start Module 1 — takes 20 minutes, changes how you see the market
                </span>
            </td>
        </tr>
    </table>
</div>

<div style="background:linear-gradient(135deg,#f0f4ff,#faf5ff);border:1px solid #c7d2fe;
            border-radius:10px;padding:16px 18px;margin-bottom:24px;">
    <p style="margin:0;font-size:13px;color:#3730a3;line-height:1.65;">
        💡 <strong>Start with one thing:</strong> Open the Trading Academy and complete
        the first lesson. It takes under 20 minutes and makes every other tool on the
        platform immediately more useful.
    </p>
</div>

<div style="text-align:center;margin-bottom:24px;">
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:15px 36px;border-radius:8px;
              font-weight:700;font-size:15px;">
        Return to Your Dashboard →
    </a>
    <p style="margin:10px 0 0;font-size:12px;color:#9ca3af;">www.gopipways.com/dashboard</p>
</div>

<p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.7;">
    Questions or need help getting started? Reply to this email — we'll sort it out personally.<br>
    <a href="mailto:contact@gopipways.com" style="color:#667eea;">contact@gopipways.com</a>
</p>"""
    return (
        f"{first}, here's what's been happening on Gopipways while you were away",
        _base(content, f"Live signals. Mentorship sessions. AI analysis. It's all waiting — and it's free.")
    )


async def _run_reengagement_emails():
    """
    Daily scheduler job.
    Targets users who registered 6–8 days ago (day 7 window)
    and have never received a re-engagement email.
    Uses email_logs to prevent double-sends.
    """
    now = datetime.utcnow()
    window_start = now - timedelta(days=8)
    window_end   = now - timedelta(days=6)

    try:
        rows = await database.fetch_all(
            """
            SELECT u.id, u.email, u.full_name
            FROM users u
            WHERE u.is_active = TRUE
              AND u.created_at BETWEEN :start AND :end
              AND NOT EXISTS (
                  SELECT 1 FROM email_logs el
                  WHERE el.user_id = u.id
                    AND el.email_type = 'reengagement'
              )
            """,
            {"start": window_start, "end": window_end}
        )

        sent = 0
        for row in rows:
            subject, html = reengagement_email(row["full_name"] or "Trader")
            ok = await send_email(row["email"], subject, html)
            await log_email(row["id"], "reengagement", row["email"], ok)
            if ok:
                sent += 1
            await asyncio.sleep(0.15)  # stay within Brevo rate limits

        if sent:
            print(f"[RE-ENGAGEMENT] ✅ Sent {sent} re-engagement email(s)", flush=True)
        else:
            print(f"[RE-ENGAGEMENT] No eligible users today", flush=True)

    except Exception as e:
        print(f"[RE-ENGAGEMENT] ❌ Scheduler error: {e}", flush=True)


async def send_reengagement_task(user_id: int, email: str, full_name: str):
    """Manual trigger — send a re-engagement email to a specific user."""
    subject, html = reengagement_email(full_name)
    ok = await send_email(email, subject, html)
    await log_email(user_id, "reengagement", email, ok)
    print(f"[RE-ENGAGEMENT] {'✅' if ok else '❌'} → {email}", flush=True)


# ── Existing templates (unchanged) ────────────────────────────────────────────

def welcome_email(full_name: str) -> tuple:
    first = (full_name or "Trader").split()[0]
    content = f"""
<h2 style="margin:0 0 10px;font-size:22px;color:#111827;line-height:1.3;">
    {first}, most traders fail for one reason.<br>You just removed it.
</h2>

<p style="color:#374151;line-height:1.75;margin:0 0 16px;font-size:15px;">
    It's not intelligence. It's not effort. Most traders lose because they operate
    without structure — no clear framework, no consistent process, no one guiding them
    through the hard parts. <strong>That ends today.</strong>
</p>

<p style="color:#374151;line-height:1.75;margin:0 0 16px;font-size:15px;">
    Gopipways gives you the tools, the signals, and the mentorship that turns
    scattered, emotional trading into a structured, repeatable approach.
    Everything you need is in one place — and it's waiting for you right now.
</p>

<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;
            padding:13px 16px;margin-bottom:24px;display:flex;align-items:center;gap:12px;">
    <div style="font-size:22px;flex-shrink:0;">👥</div>
    <p style="margin:0;font-size:13px;color:#374151;line-height:1.6;">
        <strong style="color:#111827;">Join thousands of traders</strong> across Nigeria and West Africa
        who are already using Gopipways to trade with structure, clarity, and confidence.
        You're in good company — and you're not starting from zero.
    </p>
</div>

<div style="background:linear-gradient(135deg,#f0f4ff,#faf5ff);border:1px solid #c7d2fe;
            border-radius:10px;padding:20px 22px;margin-bottom:28px;">
    <p style="margin:0 0 6px;font-size:12px;color:#6366f1;text-transform:uppercase;
              letter-spacing:.07em;font-weight:700;">Your first move</p>
    <p style="margin:0;font-size:14px;color:#1e1b4b;line-height:1.65;">
        Head to the <strong>Trading Academy</strong> and start Module 1.
        It takes under 20 minutes and permanently changes how you see the market.
        Every signal and tool on this platform will make far more sense once you do it.
    </p>
</div>

<p style="color:#374151;font-size:14px;font-weight:700;margin:0 0 14px;">
    Everything included in your account:
</p>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
    <tr style="border-bottom:1px solid #f3f4f6;">
        <td style="padding:13px 10px;">
            <strong style="color:#111827;font-size:14px;">🎓 Live Mentorship Sessions</strong><br>
            <span style="color:#6b7280;font-size:13px;line-height:1.6;">
                Learn directly from experienced traders in real time. Ask real questions,
                get real answers. Skip the years of costly trial and error.
            </span>
        </td>
    </tr>
    <tr style="border-bottom:1px solid #f3f4f6;">
        <td style="padding:13px 10px;">
            <strong style="color:#111827;font-size:14px;">📚 Trading Academy</strong><br>
            <span style="color:#6b7280;font-size:13px;line-height:1.6;">
                A structured learning path from the fundamentals to advanced market structure.
                Progress tracking, quizzes, and certificates — completely free.
            </span>
        </td>
    </tr>
    <tr style="border-bottom:1px solid #f3f4f6;">
        <td style="padding:13px 10px;">
            <strong style="color:#111827;font-size:14px;">📊 Live Trading Signals</strong><br>
            <span style="color:#6b7280;font-size:13px;line-height:1.6;">
                High-quality trade setups with entry, stop loss, take profit, and the
                full reasoning behind every position. No guesswork — just clarity.
            </span>
        </td>
    </tr>
    <tr style="border-bottom:1px solid #f3f4f6;">
        <td style="padding:13px 10px;">
            <strong style="color:#111827;font-size:14px;">🔍 AI Chart Analysis</strong><br>
            <span style="color:#6b7280;font-size:13px;line-height:1.6;">
                Upload any chart and receive professional-level analysis instantly —
                market bias, key levels, and a clear trade setup in seconds.
            </span>
        </td>
    </tr>
    <tr style="border-bottom:1px solid #f3f4f6;">
        <td style="padding:13px 10px;">
            <strong style="color:#111827;font-size:14px;">💰 Risk Calculator</strong><br>
            <span style="color:#6b7280;font-size:13px;line-height:1.6;">
                Calculate the right position size for any instrument automatically.
                Protect your capital on every trade — no spreadsheets needed.
            </span>
        </td>
    </tr>
    <tr>
        <td style="padding:13px 10px;">
            <strong style="color:#111827;font-size:14px;">🤖 AI Trading Mentor</strong><br>
            <span style="color:#6b7280;font-size:13px;line-height:1.6;">
                24/7 guidance on setups, risk, and trading psychology.
                Get clarity on any question, any time — no waiting, no judgment.
            </span>
        </td>
    </tr>
</table>

<div style="text-align:center;margin-bottom:28px;">
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:15px 36px;border-radius:8px;
              font-weight:700;font-size:15px;letter-spacing:.02em;">
        Start Your First Lesson — Free →
    </a>
    <p style="margin:10px 0 0;font-size:12px;color:#9ca3af;">www.gopipways.com/dashboard</p>
</div>

<p style="margin:0;font-size:13px;color:#9ca3af;line-height:1.7;">
    You're not doing this alone. Reply to this email anytime — we read every message.<br>
    Or reach us at <a href="mailto:contact@gopipways.com" style="color:#667eea;">contact@gopipways.com</a>
</p>"""
    return (
        f"{first}, you just removed the #1 reason traders fail",
        _base(content, f"Structure. Mentorship. Real signals. Everything you were missing is now inside.")
    )


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
        {f'<span style="font-size:12px;color:#667eea;font-weight:700;">{progress_pct}% complete</span>' if progress_pct else ''}
    </div>
    {f'<div style="background:#e5e7eb;border-radius:9999px;height:7px;"><div style="background:linear-gradient(90deg,#667eea,#764ba2);height:7px;border-radius:9999px;width:{progress_pct}%;transition:width .6s;"></div></div>' if progress_pct else ''}
</div>""" if progress_pct else ""

    next_block = f"""
<div style="background:#eff6ff;border-radius:10px;padding:18px 20px;margin:20px 0;
            border-left:4px solid #3b82f6;">
    <p style="margin:0 0 4px;font-size:11px;color:#6b7280;text-transform:uppercase;
              letter-spacing:.06em;font-weight:600;">Up next</p>
    <p style="margin:0 0 14px;font-size:15px;color:#1e3a8a;font-weight:700;">{next_lesson}</p>
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:#3b82f6;color:white;text-decoration:none;
              padding:10px 22px;border-radius:7px;font-size:14px;font-weight:700;">
        Continue Learning →
    </a>
</div>
<p style="font-size:12px;color:#9ca3af;margin:0;text-align:center;font-style:italic;">
    The traders who don't stop here are the ones who trade differently six months from now.
</p>""" if next_lesson else f"""
<div style="text-align:center;margin:20px 0;">
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:#3b82f6;color:white;text-decoration:none;
              padding:13px 26px;border-radius:8px;font-size:14px;font-weight:700;">
        Go to Academy →
    </a>
</div>"""

    content = f"""
<div style="background:linear-gradient(135deg,#f0fdf4,#ecfdf5);border-left:4px solid #10b981;
            border-radius:0 10px 10px 0;padding:16px 18px;margin-bottom:22px;">
    <p style="margin:0;font-size:14px;color:#065f46;font-weight:600;line-height:1.6;">
        {first} — consistency is the rarest skill in trading.
        You just demonstrated it. That matters more than any single trade.
    </p>
</div>

<p style="color:#374151;margin:0 0 6px;font-size:14px;">You completed:</p>
<div style="background:#f8fafc;border-radius:10px;padding:18px 20px;margin:10px 0 0;
            border-left:4px solid #10b981;">
    <p style="margin:0 0 2px;font-size:12px;color:#6b7280;">{module_title}</p>
    <p style="margin:4px 0 0;font-size:18px;font-weight:800;color:#111827;">{lesson_title}</p>
    {progress_bar}
</div>

{next_block}"""

    return (
        f"✅ Lesson complete — you're building what most traders never have",
        _base(content, f"One more step toward trading with clarity. Here's what comes next.")
    )


def certificate_email(full_name: str, course_title: str, cert_number: str) -> tuple:
    first = (full_name or "Trader").split()[0]
    content = f"""
<div style="text-align:center;margin-bottom:28px;">
    <div style="font-size:60px;line-height:1;margin-bottom:4px;">🏆</div>
    <h2 style="margin:16px 0 10px;font-size:26px;color:#111827;font-weight:800;line-height:1.3;">
        {first}, you finished what most traders never start properly.
    </h2>
    <p style="color:#374151;margin:0;font-size:15px;line-height:1.7;max-width:460px;
              display:inline-block;text-align:center;">
        The market does not reward the most talented. It rewards the most prepared.
        You just became more prepared than the vast majority of retail traders in this market.
    </p>
</div>

<div style="background:linear-gradient(135deg,#fefce8,#fef9c3);border:2px solid #fde68a;
            border-radius:12px;padding:28px;text-align:center;margin-bottom:24px;">
    <p style="margin:0 0 8px;font-size:11px;color:#92400e;text-transform:uppercase;
              letter-spacing:.09em;font-weight:700;">
        Certificate of Completion
    </p>
    <p style="margin:0 0 10px;font-size:21px;font-weight:800;color:#111827;">{course_title}</p>
    <p style="margin:0;font-size:13px;color:#b45309;font-family:monospace;letter-spacing:.04em;">
        Certificate ID: <strong>{cert_number}</strong>
    </p>
</div>

<div style="background:#f8fafc;border-radius:10px;padding:18px 20px;margin-bottom:24px;
            border-left:4px solid #667eea;">
    <p style="margin:0 0 6px;font-size:14px;color:#111827;font-weight:700;">
        What separates you now:
    </p>
    <p style="margin:0;font-size:13px;color:#374151;line-height:1.7;">
        You understand market structure, risk, and the discipline required to trade it.
        Most retail traders have none of those three. You now have all of them.
        The next step is applying it — and the live signals are the perfect place to start.
    </p>
</div>

<div style="background:linear-gradient(135deg,#fef3c7,#fffbeb);border:1px solid #fde68a;
            border-radius:8px;padding:14px 18px;margin-bottom:24px;">
    <p style="margin:0;font-size:13px;color:#92400e;line-height:1.6;">
        ⚡ <strong>The window matters.</strong> The traders who apply their knowledge
        immediately retain it and improve faster. Don't let this sit. Go trade.
    </p>
</div>

<div style="text-align:center;margin-bottom:20px;">
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:14px 32px;border-radius:8px;
              font-weight:700;font-size:15px;">
        See Today's Live Signals →
    </a>
    <p style="margin:10px 0 0;font-size:12px;color:#9ca3af;">www.gopipways.com/dashboard</p>
</div>

<p style="font-size:13px;color:#9ca3af;text-align:center;margin:0;">
    You've earned this. Now go put it to work.
</p>"""
    return (
        f"🏆 {first}, you finished what most traders never start properly",
        _base(content, f"Your certificate is ready. The market rewards the prepared — and you are.")
    )


def new_signal_email(full_name: str, symbol: str, direction: str,
                     entry: float, sl: float, tp: float,
                     confidence: int = 0, timeframe: str = "H1",
                     rationale: str = "",
                     signal_id: Optional[int] = None) -> tuple:
    first     = (full_name or "Trader").split()[0]
    color     = "#16a34a" if direction.upper() == "BUY" else "#dc2626"
    bg_color  = "#f0fdf4" if direction.upper() == "BUY" else "#fef2f2"
    dir_label = "🟢 BUY" if direction.upper() == "BUY" else "🔴 SELL"
    rr        = round(abs(tp - entry) / abs(entry - sl), 2) if abs(entry - sl) > 0 else 0
    conf_label     = f"{confidence}%" if confidence else ""
    direction_upper = direction.upper()
    signal_url      = (
        f"{DASHBOARD_URL}#enhanced-signals?signal={signal_id}"
        if signal_id else
        f"{DASHBOARD_URL}#enhanced-signals"
    )

    content = f"""
<div style="background:#fff8f0;border:1px solid #fed7aa;border-radius:8px;
            padding:12px 16px;margin-bottom:20px;">
    <p style="margin:0;font-size:12px;color:#7c2d12;line-height:1.6;">
        <strong>⚠️ Important:</strong> This notification is for informational purposes only.
        It is not financial advice, a recommendation, or a solicitation to buy or sell any instrument.
        All trading decisions are yours alone. Capital is at risk.
        Always conduct your own analysis before acting on any information.
    </p>
</div>

<h2 style="margin:0 0 6px;font-size:20px;color:#111827;font-weight:800;">
    A new signal card has been posted on your dashboard.
</h2>
<p style="color:#374151;line-height:1.75;margin:0 0 22px;font-size:15px;">
    Our analysts have identified a developing setup on <strong>{symbol}</strong>.
    The full details — market context, key levels, and reasoning — are available
    on your signal card. Review it carefully before making any decision.
</p>

<div style="background:{bg_color};border:1px solid {color}33;border-radius:12px;
            padding:24px;text-align:center;margin-bottom:22px;">
    <p style="margin:0 0 6px;font-size:11px;color:#6b7280;text-transform:uppercase;
              letter-spacing:.08em;font-weight:600;">Signal Posted</p>
    <h3 style="margin:0 0 8px;font-size:34px;font-weight:800;color:#111827;">{symbol}</h3>
    <p style="margin:0 0 4px;font-size:18px;font-weight:700;color:{color};">{dir_label}</p>
    <p style="margin:8px 0 0;font-size:13px;color:#6b7280;">
        {timeframe} timeframe
        {f'&nbsp;·&nbsp;<span style="color:#7c3aed;font-weight:600;">{conf_label} confidence</span>' if confidence else ''}
    </p>
</div>

<div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;
            padding:16px 18px;margin-bottom:22px;">
    <p style="margin:0 0 8px;font-size:13px;color:#111827;font-weight:700;">
        What to do next:
    </p>
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#374151;vertical-align:top;">
                <span style="color:#667eea;font-weight:700;margin-right:8px;">1.</span>
                Open the signal card on your dashboard
            </td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#374151;vertical-align:top;">
                <span style="color:#667eea;font-weight:700;margin-right:8px;">2.</span>
                Read the full analysis and market context
            </td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#374151;vertical-align:top;">
                <span style="color:#667eea;font-weight:700;margin-right:8px;">3.</span>
                Assess whether it fits your own trading plan and risk tolerance
            </td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#374151;vertical-align:top;">
                <span style="color:#667eea;font-weight:700;margin-right:8px;">4.</span>
                Only then decide — with your own judgement — whether to act
            </td>
        </tr>
    </table>
</div>

<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
            padding:13px 16px;margin-bottom:22px;">
    <p style="margin:0;font-size:13px;color:#92400e;line-height:1.6;">
        <strong>Discipline reminder:</strong> Never enter a trade solely because a signal appeared.
        A setup that does not align with your plan is not your setup.
        Patience is a position.
    </p>
</div>

<div style="text-align:center;margin-bottom:22px;">
    <a href="{signal_url}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:14px 34px;border-radius:8px;
              font-weight:700;font-size:15px;">
        View the Signal Card →
    </a>
    <p style="margin:10px 0 0;font-size:12px;color:#9ca3af;">
        Dashboard → Enhanced Signals
    </p>
</div>

<div style="border-top:1px solid #f3f4f6;padding-top:16px;margin-top:4px;">
    <p style="margin:0;font-size:11px;color:#9ca3af;line-height:1.8;text-align:center;">
        <strong style="color:#6b7280;">Disclaimer:</strong>
        Gopipways does not provide financial advice. Signal notifications are for
        educational and informational purposes only. Past performance of any analysis
        does not guarantee future results. Trading financial instruments carries a high
        level of risk and may not be suitable for all investors. You are solely
        responsible for your own trading decisions and any resulting gains or losses.
        Never risk money you cannot afford to lose.
    </p>
</div>"""
    return (
        f"New signal posted — {symbol} | {timeframe} | Review on your dashboard",
        _base(content, f"A {symbol} signal card has been posted. Review the full analysis before making any decision.")
    )


def subscription_email(full_name: str, plan: str, amount: str,
                       billing_cycle: str = "monthly") -> tuple:
    first = (full_name or "Trader").split()[0]
    plan_label = plan.upper()
    features = {
        "pro": [
            ("🎓 Live Mentorship Sessions", "Direct access to experienced traders — live sessions where you can ask questions, review your trades, and get real-time guidance. This alone is worth the subscription."),
            ("📊 Unlimited Live Signals", "High-quality, well-reasoned trade setups delivered daily. Entry, stop loss, take profit, and the full rationale behind every call."),
            ("🔍 Unlimited AI Chart Analysis", "Upload any chart at any time. Get professional-level analysis — market structure, key levels, and trade setup — in seconds."),
            ("📈 Advanced Performance Analytics", "Upload your trade history and find exactly where you're losing money. Most traders never diagnose their own weaknesses. You will."),
            ("🤖 Priority AI Mentor", "Instant answers to any trading question — strategy, risk, psychology. Faster responses, deeper analysis, always available."),
            ("📚 Full Academy Access", "Every lesson, every module. Build the foundational knowledge that makes every other tool more powerful."),
        ],
        "basic": [
            ("🎓 Mentorship Session Access", "Join live mentorship sessions and ask questions directly. The fastest way to compress your learning curve."),
            ("📊 Daily Live Signals", "Up to 10 high-quality setups per day — full entry, stop loss, take profit, and reasoning included."),
            ("🔍 AI Chart Analysis", "5 chart uploads per day. Professional-level analysis on any instrument, any timeframe."),
            ("📚 Full Academy Access", "All lessons and modules. Build structure into your trading from day one."),
            ("🤖 AI Mentor", "Ask anything, any time. Trading questions answered with the depth of a professional coach."),
        ],
    }
    feature_list  = features.get(plan.lower(), features["pro"])
    features_html = "".join(f"""
<tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:13px 10px;">
        <strong style="color:#111827;font-size:14px;">{icon_title}</strong><br>
        <span style="color:#6b7280;font-size:13px;line-height:1.6;">{desc}</span>
    </td>
</tr>""" for icon_title, desc in feature_list)

    content = f"""
<h2 style="margin:0 0 10px;font-size:22px;color:#111827;font-weight:800;line-height:1.3;">
    {first}, your {plan_label} plan is active. Here's what that means.
</h2>

<p style="color:#374151;line-height:1.75;margin:0 0 20px;font-size:15px;">
    Most traders spend years making expensive mistakes that mentorship and structure
    could have prevented in months. You just invested in both.
    That decision will show up in your trading.
</p>

<div style="background:linear-gradient(135deg,#667eea18,#764ba212);border:1px solid #667eea35;
            border-radius:12px;padding:22px;text-align:center;margin-bottom:22px;">
    <p style="margin:0 0 4px;font-size:12px;color:#6b7280;font-weight:600;">Your active plan</p>
    <p style="margin:0 0 6px;font-size:24px;font-weight:800;color:#111827;">
        Gopipways {plan_label}
    </p>
    <p style="margin:0;font-size:15px;color:#667eea;font-weight:700;">{amount} / {billing_cycle}</p>
</div>

<div style="background:#fef3c7;border:1px solid #fde68a;border-radius:9px;
            padding:16px 18px;margin-bottom:22px;">
    <p style="margin:0;font-size:13px;color:#92400e;line-height:1.7;">
        💡 <strong>The ROI framing that matters:</strong> One well-executed, well-sized trade
        can return many times the cost of your subscription. The mentorship, the signals,
        and the analysis are not expenses — they are the inputs that make that possible.
    </p>
</div>

<p style="color:#374151;font-size:14px;font-weight:700;margin:0 0 14px;">
    What's now unlocked for you:
</p>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:26px;">
    {features_html}
</table>

<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:9px;
            padding:16px 18px;margin-bottom:24px;">
    <p style="margin:0 0 6px;font-size:14px;color:#065f46;font-weight:700;">
        Start here — right now:
    </p>
    <p style="margin:0;font-size:13px;color:#374151;line-height:1.65;">
        Check today's live signals on your dashboard, or join the next mentorship session.
        Both are live and waiting. The faster you engage, the faster you improve.
    </p>
</div>

<div style="text-align:center;margin-bottom:22px;">
    <a href="{DASHBOARD_URL}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:15px 34px;border-radius:8px;
              font-weight:700;font-size:15px;">
        Go to Your Dashboard →
    </a>
    <p style="margin:10px 0 0;font-size:12px;color:#9ca3af;">www.gopipways.com/dashboard</p>
</div>

<p style="font-size:13px;color:#9ca3af;line-height:1.6;margin:0;">
    Questions about your plan? Reply to this email or contact
    <a href="mailto:contact@gopipways.com" style="color:#667eea;">contact@gopipways.com</a>
</p>"""
    return (
        f"Your Gopipways {plan_label} plan is active — here's how to make it count",
        _base(content, f"Mentorship. Signals. Structure. Everything you need to trade better starts now.")
    )


def blog_published_email(full_name: str, post_title: str, post_excerpt: str,
                          post_slug: str, category: str = "Trading",
                          read_time: str = "5 min") -> tuple:
    first    = (full_name or "Trader").split()[0]
    post_url = f"{APP_BASE_URL}/blog/{post_slug}" if post_slug else DASHBOARD_URL

    content = f"""
<p style="margin:0 0 6px;font-size:12px;color:#667eea;font-weight:700;
          text-transform:uppercase;letter-spacing:.07em;">
    {category} · {read_time} read
</p>

<h2 style="margin:0 0 14px;font-size:21px;font-weight:800;color:#111827;line-height:1.35;">
    {post_title}
</h2>

<p style="color:#374151;line-height:1.75;margin:0 0 20px;font-size:15px;">
    {first}, what you learn in the next few minutes could change how you approach
    your next trade — and every one after it.
</p>

<div style="border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:24px;">
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:10px 18px;">
        <span style="color:rgba(255,255,255,.9);font-size:12px;font-weight:700;
                     text-transform:uppercase;letter-spacing:.06em;">
            Latest from Gopipways Research
        </span>
    </div>
    <div style="padding:24px 22px;">
        <p style="margin:0 0 18px;color:#6b7280;font-size:14px;line-height:1.75;">
            {post_excerpt}
        </p>
        <a href="{post_url}"
           style="display:inline-block;background:#111827;color:white;text-decoration:none;
                  padding:12px 24px;border-radius:7px;font-weight:700;font-size:14px;">
            Read the Full Article →
        </a>
    </div>
</div>

<p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
    You're receiving this because you're a registered Gopipways member.
</p>"""
    return (
        post_title,
        _base(content, f"New insight from Gopipways: {post_title} — {read_time} read.")
    )


def password_reset_email(full_name: str, reset_url: str) -> tuple:
    first = (full_name or "Trader").split()[0]
    content = f"""
<h2 style="margin:0 0 10px;font-size:22px;color:#111827;font-weight:800;">
    Let's get you back in, {first}.
</h2>
<p style="color:#374151;line-height:1.75;margin:0 0 26px;font-size:15px;">
    No problem — it happens to everyone. Click below to set a new password
    and get straight back to your dashboard.
</p>

<div style="text-align:center;margin:28px 0;">
    <a href="{reset_url}"
       style="display:inline-block;background:linear-gradient(135deg,#667eea,#764ba2);
              color:white;text-decoration:none;padding:15px 34px;border-radius:8px;
              font-weight:700;font-size:15px;">
        Reset My Password →
    </a>
    <p style="margin:12px 0 0;font-size:12px;color:#9ca3af;">
        This link works <strong style="color:#374151;">once</strong> and expires in
        <strong style="color:#374151;">1 hour</strong>.
    </p>
</div>

<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:9px;
            padding:16px 18px;margin-bottom:20px;">
    <p style="margin:0;font-size:13px;color:#6b7280;line-height:1.7;">
        🔒 <strong style="color:#374151;">Didn't request this?</strong><br>
        Your account is secure — nothing has changed. You can safely ignore this email.
    </p>
</div>

<p style="font-size:13px;color:#9ca3af;line-height:1.6;margin:0;">
    If the button above doesn't work, contact us at
    <a href="mailto:contact@gopipways.com" style="color:#667eea;">contact@gopipways.com</a>
</p>"""
    return (
        f"Reset your Gopipways password — link expires in 1 hour",
        _base(content, f"Your reset link is inside. It expires in 1 hour — click now.")
    )


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
    try:
        row = await database.fetch_one(
            "SELECT preferences FROM user_email_preferences WHERE user_id = :uid",
            {"uid": user_id}
        )
        if row:
            prefs = json.loads(row["preferences"] or "{}")
            if not prefs.get("signal_alerts", False):
                return
    except Exception:
        pass
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
    email = body.email.lower().strip()

    try:
        recent_count = await database.fetch_one(
            "SELECT COUNT(*) as cnt FROM password_reset_tokens "
            "WHERE email = :email AND created_at > NOW() - INTERVAL '1 hour'",
            {"email": email}
        )
        if recent_count and recent_count["cnt"] >= 3:
            return {"success": True, "message": "If that email is registered, a reset link has been sent."}
    except Exception:
        pass

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

        try:
            await database.execute(
                "UPDATE password_reset_tokens SET used = TRUE "
                "WHERE user_id = :uid AND used = FALSE",
                {"uid": user_id}
            )
        except Exception:
            pass

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

        reset_url = f"{APP_BASE_URL}/dashboard.html?reset_token={raw_token}"
        subject, html = password_reset_email(full_name, reset_url)
        ok = await send_email(email, subject, html)
        await log_email(user_id, "password_reset", email, ok)
        print(f"[EMAIL/RESET] Reset link sent to {email} (user_id={user_id}, token={raw_token[:8]}...)", flush=True)

    return {"success": True, "message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    import bcrypt

    if not body.token or len(body.new_password) < 8:
        raise HTTPException(400, "Token is required and password must be at least 8 characters.")

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

    expires_at = row["expires_at"]
    if hasattr(expires_at, "tzinfo") and expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)
    if datetime.utcnow() > expires_at:
        raise HTTPException(400, "This reset link has expired (links are valid for 1 hour). Please request a new one.")

    hashed = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()

    try:
        await database.execute(
            "UPDATE users SET password_hash = :pw WHERE id = :uid",
            {"pw": hashed, "uid": row["user_id"]}
        )
    except Exception as e:
        print(f"[EMAIL/RESET] Failed to update password: {e}", flush=True)
        raise HTTPException(500, "Failed to update password. Please try again.")

    await database.execute(
        "UPDATE password_reset_tokens SET used = TRUE WHERE token = :token",
        {"token": body.token}
    )

    print(f"[EMAIL/RESET] Password reset successful for user_id={row['user_id']}", flush=True)
    return {"success": True, "message": "Password updated successfully. You can now log in."}


@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
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
    <td style="padding:10px 8px;">📚 <strong>Trading Academy</strong> — structured curriculum, quizzes and certificates</td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:10px 8px;">📊 <strong>Live Signals</strong> — Real institutional-grade trade setups</td>
  </tr>
  <tr style="border-bottom:1px solid #f3f4f6;">
    <td style="padding:10px 8px;">💰 <strong>Risk Calculator</strong> — Proper position sizing every time</td>
  </tr>
  <tr>
    <td style="padding:10px 8px;">🤖 <strong>AI Mentor</strong> — trading questions answered instantly — strategy, risk, psychology</td>
  </tr>
</table>
<div style="text-align:center;margin-bottom:20px;">
  <a href="{DASHBOARD_URL}"
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
    await log_email(0, "capture", body.email, ok)
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
        "welcome":              lambda: welcome_email("Test User"),
        "lesson_complete":      lambda: lesson_complete_email("Test User", "Introduction to Market Structure", "Beginner Module", "Reading Price Action"),
        "certificate":          lambda: certificate_email("Test User", "Advanced Market Structure Trading", "GP-2026-001"),
        "signal":               lambda: new_signal_email("Test User", "XAUUSD", "BUY", 4525.0, 4450.0, 4650.0, confidence=85, timeframe="H1", rationale="Price confirmed a break of structure at 4600 with a well-defined order block at 4525 in a discount zone following a liquidity sweep.", signal_id=999),
        "subscription":         lambda: subscription_email("Test User", "Pro", "₦15,000", "monthly"),
        "blog":                 lambda: blog_published_email("Test User", "How a Structured Trading Approach Changes Everything", "Most retail traders lose not from lack of effort, but from lack of structure.", "structured-trading-approach", "Trading Education", "6 min"),
        "password_reset":       lambda: password_reset_email("Test User", f"{APP_BASE_URL}/dashboard.html?reset_token=TEST_TOKEN_EXAMPLE"),
        "webinar_confirmation": lambda: webinar_confirmation_email("Test User", "Live Trading Session — Reading Market Structure", "Aaron", datetime.utcnow() + timedelta(days=2), 90),
        "webinar_reminder_24h": lambda: webinar_reminder_email("Test User", "Live Trading Session — Reading Market Structure", "Aaron", datetime.utcnow() + timedelta(hours=24), 90, "24h"),
        "webinar_reminder_1h":  lambda: webinar_reminder_email("Test User", "Live Trading Session — Reading Market Structure", "Aaron", datetime.utcnow() + timedelta(hours=1), 90, "1h"),
        "reengagement":         lambda: reengagement_email("Test User"),
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
            first_name = (row["full_name"] or "Trader").split()[0]
            user_id    = row["id"]

            greeting = f"""
<p style="margin:0 0 20px;color:#374151;font-size:15px;">
  Hi <strong>{first_name}</strong>,
</p>"""

            unsubscribe = f"""
<div style="text-align:center;margin-top:24px;padding-top:16px;border-top:1px solid #e5e7eb;">
  <p style="margin:0;font-size:12px;color:#9ca3af;">
    You're receiving this as a registered Gopipways user.<br>
    <a href="{DASHBOARD_URL}" style="color:#6b7280;">
      Manage email preferences
    </a>
  </p>
</div>"""

            personalised_body = html_body.replace("{{first_name}}", first_name)
            full_html = _base(greeting + personalised_body + unsubscribe)

            ok = await send_email(row["email"], subject, full_html)
            if ok:
                sent += 1
                await log_email(user_id, "broadcast", row["email"], True)
            else:
                failed += 1
                await log_email(user_id, "broadcast", row["email"], False)
            await asyncio.sleep(0.1)

        print(f"[EMAIL BROADCAST] ✅ Complete — {sent} sent, {failed} failed out of {len(rows)}", flush=True)

    background_tasks.add_task(_send_all)
    return {"status": "queued", "filter": tier,
            "message": "Broadcast started in background. Check Railway logs for progress."}
