"""
Admin panel API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from backend.security import get_current_user
from backend.database import database, users

router = APIRouter()

async def get_admin_user(current_user = Depends(get_current_user)):
    """Verify user is admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/users")
async def list_all_users(admin = Depends(get_admin_user)):
    """List all users (admin only)."""
    return {"users": [], "admin": admin["email"]}
