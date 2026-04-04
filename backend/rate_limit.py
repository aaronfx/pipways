"""
Rate limiting for Pipways API.

Uses slowapi with in-memory storage (no Redis required).
Apply the limiter to individual routes or as middleware.

Usage in route files:
    from .rate_limit import limiter

    @router.post("/expensive-endpoint")
    @limiter.limit("5/minute")
    async def expensive(request: Request):
        ...
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request


def _get_key(request: Request) -> str:
    """
    Rate-limit key function.
    Uses the authenticated user's email from the JWT if available,
    otherwise falls back to the client IP address.
    This prevents a single user from exhausting limits across IPs
    and keeps unauthenticated endpoints keyed by IP.
    """
    # Try to extract user from already-decoded auth state
    # (set by FastAPI's Depends(get_current_user) before the limiter fires)
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user.get("email", get_remote_address(request))
    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_key,
    default_limits=["200/minute"],          # generous global default
    storage_uri="memory://",                # no Redis dependency
)


def install_rate_limiter(app):
    """
    Call once from main.py to wire up the limiter and error handler.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
