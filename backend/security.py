"""
Authentication and security utilities.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# FIXED: Use relative imports to work correctly as a package
from .database import database, users, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# get_current_user: canonical implementation is in auth.py.
# This wrapper re-exports it for backward compatibility with modules
# that import from security. Uses lazy import to avoid circular dependency
# (auth.py imports verify_password etc. from security.py).
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Delegates to auth.get_current_user — single source of truth."""
    from .auth import get_current_user as _auth_get_current_user
    return await _auth_get_current_user(token)


# ══════════════════════════════════════════════════════════════════════════════
# SHARED USER-OBJECT HELPERS
# Import these in every route file instead of repeating the pattern inline.
# ══════════════════════════════════════════════════════════════════════════════

def get_user_id(user) -> int | None:
    """
    Safely extract the integer user ID from any user object type:
      - SQLAlchemy Row   → user._mapping["id"]
      - Plain dict       → user["id"]
      - ORM model        → user.id
    Returns None if the field is missing.
    """
    if hasattr(user, '_mapping'):
        return user._mapping.get("id")
    if isinstance(user, dict):
        return user.get("id")
    return getattr(user, "id", None)


def get_user_attr(user, attr: str, default=None):
    """
    Safely read any attribute from a user object.
    Covers SQLAlchemy Row, dict, and ORM model instances.
    """
    if hasattr(user, '_mapping'):
        return user._mapping.get(attr, default)
    if isinstance(user, dict):
        return user.get(attr, default)
    return getattr(user, attr, default)


def is_admin_user(user) -> bool:
    """
    Return True if the user has admin privileges.
    Accepts is_admin=True, role='admin', or is_superuser=True.
    """
    return (
        bool(get_user_attr(user, "is_admin", False))
        or get_user_attr(user, "role") == "admin"
        or bool(get_user_attr(user, "is_superuser", False))
    )
