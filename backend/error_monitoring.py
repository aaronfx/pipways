"""
Sentry error monitoring integration for Gopipways.

Environment variables:
- SENTRY_DSN: Sentry Data Source Name (required to enable monitoring)
- ALERT_EMAIL: Email address for alerts (default: akwuaaron60@gmail.com)
- APP_ENV: Environment name (default: production)
- APP_VERSION: Application version (set in main.py)
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Optional, Dict, Any


def init_sentry(app: FastAPI, release: Optional[str] = None) -> None:
    """
    Initialize Sentry error monitoring for the FastAPI application.

    Args:
        app: FastAPI application instance
        release: Application release version (if not provided, will attempt to get from environment)
    """
    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()

    # Skip initialization if SENTRY_DSN is not set
    if not sentry_dsn:
        print("[SENTRY] SENTRY_DSN not configured, error monitoring disabled", flush=True)
        return

    alert_email = os.getenv("ALERT_EMAIL", "akwuaaron60@gmail.com").strip()
    app_env = os.getenv("APP_ENV", "production").strip()

    # Use provided release or try to get from environment
    if not release:
        release = os.getenv("APP_VERSION", "unknown")

    def before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Hook to process events before sending to Sentry.
        Tags errors with severity levels.
        """
        # Determine severity based on exception type
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            # Tag critical exceptions
            if exc_type and "Critical" in exc_type.__name__:
                event.setdefault("tags", {})["severity"] = "critical"
            elif exc_type and "Error" in exc_type.__name__:
                event.setdefault("tags", {})["severity"] = "error"
            else:
                event.setdefault("tags", {})["severity"] = "warning"

        # Add custom context
        event.setdefault("tags", {})["alert_email"] = alert_email

        return event

    # Initialize Sentry SDK
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FastApiIntegration(),
        ],
        traces_sample_rate=0.1,  # Sample 10% of transactions for performance monitoring
        environment=app_env,
        release=release,
        before_send=before_send,
    )

    print(f"[SENTRY] Initialized with DSN in {app_env} environment (release: {release})", flush=True)

    # Add custom exception handler for 500 errors
    @app.exception_handler(500)
    async def sentry_error_handler(request: Request, exc: Exception):
        """
        Custom exception handler that captures 500 errors to Sentry
        and returns appropriate response.
        """
        # Capture to Sentry with additional context
        sentry_sdk.capture_exception(exc, tags={"endpoint": request.url.path})

        # Return appropriate response based on request type
        if any(request.url.path.startswith(p) for p in ("/api", "/auth")):
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "error_id": sentry_sdk.last_event_id()}
            )

        return HTMLResponse(
            content=f"""<!DOCTYPE html><html>
            <head><title>Server Error — Gopipways</title></head>
            <body style="font-family:Arial,sans-serif;text-align:center;padding:80px;background:#0f172a;color:#e2e8f0;">
              <h1 style="color:#ef4444;">Something went wrong</h1>
              <p style="color:#94a3b8;">We're working to fix this. Please try again later.</p>
              {f'<p style="font-size:12px;color:#64748b;">Error ID: {sentry_sdk.last_event_id()}</p>' if sentry_sdk.last_event_id() else ''}
              <a href="/" style="display:inline-block;margin-top:20px;background:#7c3aed;color:white;
                 padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">
                Back to Home
              </a>
            </body></html>""",
            status_code=500
        )


def capture_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Manually capture an error to Sentry.

    Args:
        error: The exception to capture
        context: Optional dictionary with additional context data

    Returns:
        Event ID from Sentry if captured, None otherwise
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            return sentry_sdk.capture_exception(error)
    else:
        return sentry_sdk.capture_exception(error)
