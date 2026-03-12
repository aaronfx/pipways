"""
Enhanced blog features (SEO, comments, tags).
"""
from fastapi import APIRouter, Depends
from backend.security import get_current_user
from backend.database import database

router = APIRouter()

@router.get("/enhanced/posts")
async def enhanced_posts():
    """Get posts with enhanced metadata."""
    return {"posts": [], "features": ["seo", "comments", "tags"]}

@router.post("/enhanced/posts/{post_id}/comment")
async def add_comment(post_id: int, comment: str, current_user = Depends(get_current_user)):
    """Add comment to blog post."""
    return {"post_id": post_id, "comment": comment, "user": current_user["email"]}
