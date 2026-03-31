"""
Authentication module - Production Grade OAuth2 Implementation
Updated: /auth/me returns subscription tier + full usage state
Added: get_current_user dependency for other routers to import
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError

from .database import database, users, get_available_columns
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)

# Guard email import — email service may not be fully configured on first deploy
try:
    from .email_service import send_welcome_email_task as _send_welcome_email_task
    _EMAIL_AVAILABLE = True
except Exception:
    _EMAIL_AVAILABLE = False
    _send_welcome_email_task = None

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ═══════════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    """Base user response — returned by /token and /register (fast, no extra queries)."""
    id: int
    email: str
    full_name: str
    is_active: bool = True
    is_admin: bool = False
    subscription_tier: str = "free"


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

_available_columns_cache = None

def get_columns():
    global _available_columns_cache
    if _available_columns_cache is None:
        _available_columns_cache = get_available_columns()
    return _available_columns_cache


def _extract(user, key, default=None):
    """Safely extract field from a Row object or dict."""
    if isinstance(user, dict):
        return user.get(key, default)
    return getattr(user, key, default)


def _normalise_tier(tier: str) -> str:
    """Normalise legacy 'enterprise' to 'pro'."""
    if not tier:
        return "free"
    return "pro" if tier == "enterprise" else tier


async def get_user_by_email(email: str):
    try:
        query = users.select().where(users.c.email == email)
        return await database.fetch_one(query)
    except Exception as e:
        print(f"[DB Error] fetching user: {e}", flush=True)
        return None


async def create_user(user_data: dict):
    try:
        available_cols = get_columns()
        insert_data = {
            "email":         user_data["email"],
            "password_hash": get_password_hash(user_data["password"]),
            "created_at":    datetime.utcnow(),
        }
        if "full_name"         in available_cols: insert_data["full_name"]         = user_data.get("full_name", "")
        if "is_active"         in available_cols: insert_data["is_active"]         = True
        if "is_admin"          in available_cols: insert_data["is_admin"]          = False
        if "role"              in available_cols: insert_data["role"]              = "user"
        if "subscription_tier" in available_cols: insert_data["subscription_tier"] = "free"

        user_id = await database.execute(users.insert().values(**insert_data))
        return {
            "id":                user_id,
            "email":             user_data["email"],
            "full_name":         insert_data.get("full_name", ""),
            "is_active":         True,
            "is_admin":          False,
            "subscription_tier": "free",
        }
    except Exception as e:
        print(f"[Error] creating user: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH DEPENDENCY (for use in other routers)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency to get the current authenticated user.
    
    Import in other modules:
        from .auth import get_current_user
    
    Use in routes:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            user_id = current_user["id"]
            ...
    
    Returns dict with keys:
        id, email, full_name, is_active, is_admin, role, subscription_tier
    """
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = await get_user_by_email(email)
    if not user:
        raise cred_exc

    return {
        "id":                _extract(user, "id") or user_id,
        "email":             email,
        "full_name":         _extract(user, "full_name", ""),
        "is_active":         _extract(user, "is_active", True),
        "is_admin":          _extract(user, "is_admin", False),
        "role":              _extract(user, "role", "user"),
        "subscription_tier": _normalise_tier(_extract(user, "subscription_tier", "free")),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    print(f"[Auth] Registration: {user_data.email}", flush=True)
    if await get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await create_user({
        "email":     user_data.email,
        "password":  user_data.password,
        "full_name": user_data.full_name,
    })
    access_token = create_access_token(
        data={"sub": user_data.email, "user_id": user["id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Fire welcome email (non-blocking — doesn't delay registration response)
    if _EMAIL_AVAILABLE and _send_welcome_email_task is not None:
        try:
            import asyncio
            asyncio.create_task(
                _send_welcome_email_task(user["id"], user_data.email, user_data.full_name or "")
            )
        except Exception as e:
            print(f"[Auth] Welcome email task failed (non-fatal): {e}", flush=True)

    return {"access_token": access_token, "token_type": "bearer", "user": UserResponse(**user)}


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"[Auth] Login: {form_data.username}", flush=True)
    user = await get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})

    try:
        is_valid = verify_password(form_data.password, _extract(user, "password_hash"))
    except Exception as e:
        print(f"[Error] Password verification: {e}", flush=True)
        is_valid = False

    if not is_valid:
        raise HTTPException(status_code=401, detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})

    if not _extract(user, "is_active", True):
        raise HTTPException(status_code=400, detail="Account is deactivated")

    user_id   = _extract(user, "id")
    email     = _extract(user, "email")
    is_admin  = _extract(user, "is_admin", False)
    full_name = _extract(user, "full_name", "")
    tier      = _normalise_tier(_extract(user, "subscription_tier", "free"))

    access_token = create_access_token(
        data={"sub": email, "user_id": user_id, "is_admin": is_admin},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type":   "bearer",
        "user": UserResponse(id=user_id, email=email, full_name=full_name,
                             is_active=True, is_admin=is_admin,
                             subscription_tier=tier),
    }


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Returns the authenticated user's full profile including subscription tier
    and feature usage state. Called by usage.js on every page load.
    """
    user_id = current_user["id"]

    # Fetch full usage state — non-fatal if subscriptions module not ready
    usage_state = None
    try:
        from .subscriptions import get_usage_state
        usage_state = await get_usage_state(user_id)
    except Exception as e:
        print(f"[Auth /me] usage state load error: {e}", flush=True)

    return {
        **current_user,
        "usage": usage_state,
    }


@router.get("/usage")
async def get_usage_counts(current_user: dict = Depends(get_current_user)):
    """
    Lightweight endpoint that returns ONLY feature usage counts for the current user.
    Called by usage.js after every successful feature use to refresh the badge
    without the overhead of reloading the full user profile from /auth/me.

    Returns:
        { chart_analysis: int, ai_mentor: int, performance_analysis: int, stock_research: int }
    """
    user_id = current_user["id"]
    try:
        from .subscriptions import get_usage_state
        usage = await get_usage_state(user_id)
        print(f"[Auth /usage] user={user_id} counts={usage}", flush=True)
        return {"usage": usage}
    except Exception as e:
        print(f"[Auth /usage] error for user={user_id}: {e}", flush=True)
        return {"usage": None}
