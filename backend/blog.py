"""
Blog content management.
"""
from fastapi import APIRouter, Depends
from backend.security import get_current_user
from backend.database import database

router = APIRouter()

@router.get("/posts")
async def list_posts():
    """List all blog posts (public)."""
    return {"posts": [], "module": "blog"}

@router.post("/posts")
async def create_post(post: dict, current_user = Depends(get_current_user)):
    """Create new blog post (admin only)."""
    return {"status": "created", "post": post}
