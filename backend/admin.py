from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, update, func, desc
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import database, users, signals, courses, blog_posts, webinars, performance_analyses
from .security import get_current_admin, get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])
limiter = Limiter(key_func=get_remote_address)

class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    email_verified: Optional[bool] = None

class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_signals: int
    active_signals: int
    total_courses: int
    published_courses: int
    total_blog_posts: int
    upcoming_webinars: int
    recent_users: List[dict]

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_admin)
):
    query = select(func.count()).select_from(users)
    total_users = await database.fetch_val(query)

    query = select(func.count()).select_from(users).where(users.c.is_active == True)
    active_users = await database.fetch_val(query)

    query = select(func.count()).select_from(signals)
    total_signals = await database.fetch_val(query)

    query = select(func.count()).select_from(signals).where(signals.c.status == "ACTIVE")
    active_signals = await database.fetch_val(query)

    query = select(func.count()).select_from(courses)
    total_courses = await database.fetch_val(query)

    query = select(func.count()).select_from(courses).where(courses.c.is_published == True)
    published_courses = await database.fetch_val(query)

    query = select(func.count()).select_from(blog_posts)
    total_blog_posts = await database.fetch_val(query)

    query = select(func.count()).select_from(webinars).where(webinars.c.scheduled_at > datetime.utcnow())
    upcoming_webinars = await database.fetch_val(query)

    query = select(users).order_by(desc(users.c.created_at)).limit(5)
    recent_users = await database.fetch_all(query)

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_signals": total_signals,
        "active_signals": active_signals,
        "total_courses": total_courses,
        "published_courses": published_courses,
        "total_blog_posts": total_blog_posts,
        "upcoming_webinars": upcoming_webinars,
        "recent_users": [dict(u) for u in recent_users]
    }

@router.get("/users")
@limiter.limit("60/minute")
async def get_all_users(
    request: Request,
    is_active: Optional[bool] = Query(None),
    is_admin: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_admin)
):
    query = select(users).order_by(desc(users.c.created_at))

    if is_active is not None:
        query = query.where(users.c.is_active == is_active)
    if is_admin is not None:
        query = query.where(users.c.is_admin == is_admin)

    query = query.limit(limit).offset(offset)
    results = await database.fetch_all(query)
    return [dict(row) for row in results]

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_admin)
):
    query = select(users).where(users.c.id == user_id)
    user = await database.fetch_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    query = update(users).where(users.c.id == user_id).values(**update_data)
    await database.execute(query)

    return {"message": "User updated successfully"}

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str,
    current_user: dict = Depends(get_current_admin)
):
    query = select(users).where(users.c.id == user_id)
    user = await database.fetch_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed = get_password_hash(new_password)
    query = update(users).where(users.c.id == user_id).values(
        password_hash=hashed,
        updated_at=datetime.utcnow()
    )
    await database.execute(query)

    return {"message": "Password reset successfully"}
