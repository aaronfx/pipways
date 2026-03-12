"""
User notifications (Email, Telegram, Push).
"""
from fastapi import APIRouter, Depends
from backend.security import get_current_user

router = APIRouter()

@router.get("/")
async def get_notifications(current_user = Depends(get_current_user)):
    """Get user notifications."""
    return {"notifications": [], "unread": 0}
