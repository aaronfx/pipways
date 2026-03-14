"""
Admin panel API endpoints - FIXED
Returns proper stats and handles admin verification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from .security import get_current_user
from .database import database, users, signals

router = APIRouter()

async def get_admin_user(current_user = Depends(get_current_user)):
    """Verify user is admin."""
    # Handle both dict and object types
    is_admin = False
    if isinstance(current_user, dict):
        is_admin = current_user.get("is_admin") or current_user.get("role") == "admin"
    else:
        is_admin = getattr(current_user, 'is_admin', False) or getattr(current_user, 'role', None) == 'admin'
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/users")
async def get_admin_stats(admin = Depends(get_admin_user)):
    """Get admin dashboard stats"""
    try:
        # Get total users count
        user_count = await database.fetch_one("SELECT COUNT(*) as count FROM users")
        total_users = user_count["count"] if user_count else 0
        
        # Get active signals count
        try:
            signals_query = "SELECT COUNT(*) as count FROM signals WHERE status = 'active'"
            signals_count = await database.fetch_one(signals_query)
            active_signals = signals_count["count"] if signals_count else 0
        except:
            active_signals = 0
        
        # Get new users today
        try:
            new_query = "SELECT COUNT(*) as count FROM users WHERE created_at >= CURRENT_DATE"
            new_count = await database.fetch_one(new_query)
            new_today = new_count["count"] if new_count else 0
        except:
            new_today = 0
        
        return {
            "total_users": total_users,
            "active_signals": active_signals,
            "new_today": new_today,
            "admin_email": admin.get("email") if isinstance(admin, dict) else getattr(admin, 'email', 'admin')
        }
        
    except Exception as e:
        print(f"[ADMIN ERROR] {e}", flush=True)
        # Return default values instead of crashing
        return {
            "total_users": 0,
            "active_signals": 0,
            "new_today": 0,
            "error": str(e)
        }
