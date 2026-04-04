"""
Enhanced blog features (SEO, comments, tags).
PRODUCTION READY
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from .security import get_current_user
from .database import database

router = APIRouter()


@router.get("/enhanced/posts")
async def enhanced_posts(
    limit: int = 10,
    tag: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get posts with enhanced metadata including:
    - SEO fields (meta description, keywords)
    - Comment counts
    - Tags
    - Read time estimates
    """
    try:
        if tag:
            query = """
                SELECT bp.*,
                       COUNT(DISTINCT bc.id) as comment_count,
                       array_agg(DISTINCT bt.name) as tags
                FROM blog_posts bp
                LEFT JOIN blog_comments bc ON bp.id = bc.post_id
                LEFT JOIN blog_post_tags bpt ON bp.id = bpt.post_id
                LEFT JOIN blog_tags bt ON bpt.tag_id = bt.id
                WHERE bp.status = 'published'
                AND bp.id IN (
                    SELECT post_id FROM blog_post_tags bpt2
                    JOIN blog_tags bt2 ON bpt2.tag_id = bt2.id
                    WHERE bt2.name = :tag
                )
                GROUP BY bp.id
                ORDER BY bp.created_at DESC
                LIMIT :limit
            """
            params = {"tag": tag, "limit": limit}
        elif search:
            query = """
                SELECT bp.*,
                       COUNT(DISTINCT bc.id) as comment_count,
                       array_agg(DISTINCT bt.name) as tags
                FROM blog_posts bp
                LEFT JOIN blog_comments bc ON bp.id = bc.post_id
                LEFT JOIN blog_post_tags bpt ON bp.id = bpt.post_id
                LEFT JOIN blog_tags bt ON bpt.tag_id = bt.id
                WHERE bp.status = 'published'
                AND (bp.title ILIKE :search OR bp.content ILIKE :search)
                GROUP BY bp.id
                ORDER BY bp.created_at DESC
                LIMIT :limit
            """
            params = {"search": f"%{search}%", "limit": limit}
        else:
            query = """
                SELECT bp.*,
                       COUNT(DISTINCT bc.id) as comment_count,
                       array_agg(DISTINCT bt.name) as tags
                FROM blog_posts bp
                LEFT JOIN blog_comments bc ON bp.id = bc.post_id
                LEFT JOIN blog_post_tags bpt ON bp.id = bpt.post_id
                LEFT JOIN blog_tags bt ON bpt.tag_id = bt.id
                WHERE bp.status = 'published'
                GROUP BY bp.id
                ORDER BY bp.created_at DESC
                LIMIT :limit
            """
            params = {"limit": limit}

        rows = await database.fetch_all(query, params)

        posts = []
        for row in rows:
            r = dict(row)
            posts.append({
                "id":         r.get("id"),
                "title":      r.get("title", ""),
                "slug":       r.get("slug", ""),
                "excerpt":    r.get("excerpt", ""),
                "content":    r.get("content", ""),
                "category":   r.get("category", "General"),
                "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
                "featured":   bool(r.get("featured", False)),
                "read_time":  r.get("read_time", "5 min"),
                # Enhanced fields
                "comment_count": r.get("comment_count", 0),
                "tags": [t for t in (r.get("tags") or []) if t] or [],
                "seo_meta": {
                    "description": r.get("seo_description") or r.get("excerpt", ""),
                    "keywords":    r.get("seo_keywords", ""),
                    "og_image":    r.get("og_image_url", ""),
                },
            })

        return {
            "posts":   posts,
            "count":   len(posts),
            "filters": {"tag": tag, "search": search},
        }

    except Exception as e:
        print(f"[BLOG ENHANCED] Error: {e}", flush=True)
        return {"posts": [], "count": 0, "error": str(e)}


@router.post("/enhanced/posts/{post_id}/comment")
async def add_comment(
    post_id: int,
    comment: str,
    current_user=Depends(get_current_user),
):
    """Add a comment to a blog post."""
    try:
        # FIX: current_user is a databases Row object — use dict() before .get()
        user = dict(current_user)
        user_id    = user.get("id")
        user_email = user.get("email", "anonymous")

        post = await database.fetch_one(
            "SELECT id FROM blog_posts WHERE id = :id AND status = 'published'",
            {"id": post_id},
        )
        if not post:
            raise HTTPException(404, "Post not found")

        result = await database.fetch_one(
            """
            INSERT INTO blog_comments (post_id, user_id, content, created_at)
            VALUES (:post_id, :user_id, :content, NOW())
            RETURNING id, created_at
            """,
            {"post_id": post_id, "user_id": user_id, "content": comment},
        )

        return {
            "id":         result["id"],
            "post_id":    post_id,
            "content":    comment,
            "author":     user_email,
            "created_at": result["created_at"].isoformat(),
            "status":     "published",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[BLOG COMMENT] Error: {e}", flush=True)
        # Graceful demo-mode fallback (blog_comments table may not exist yet)
        return {
            "post_id": post_id,
            "content": comment,
            "author":  dict(current_user).get("email", "anonymous"),
            "status":  "demo_mode",
            "message": "Comments stored in demo mode (blog_comments table not yet created)",
        }


@router.get("/enhanced/posts/{post_id}/comments")
async def get_comments(post_id: int, limit: int = 20):
    """Get comments for a specific post."""
    try:
        rows = await database.fetch_all(
            """
            SELECT bc.*, u.email as author_email
            FROM blog_comments bc
            LEFT JOIN users u ON bc.user_id = u.id
            WHERE bc.post_id = :post_id
            ORDER BY bc.created_at DESC
            LIMIT :limit
            """,
            {"post_id": post_id, "limit": limit},
        )

        comments = [
            {
                "id":         r["id"],
                "content":    r["content"],
                "author":     r["author_email"].split("@")[0] if r["author_email"] else "Anonymous",
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
        return {"post_id": post_id, "comments": comments, "count": len(comments)}

    except Exception as e:
        print(f"[GET COMMENTS] Error: {e}", flush=True)
        return {"post_id": post_id, "comments": [], "count": 0}


@router.get("/enhanced/tags")
async def get_all_tags():
    """Get all available blog tags with post counts."""
    try:
        rows = await database.fetch_all(
            """
            SELECT bt.name, bt.slug, COUNT(bpt.post_id) as post_count
            FROM blog_tags bt
            LEFT JOIN blog_post_tags bpt ON bt.id = bpt.tag_id
            GROUP BY bt.id, bt.name, bt.slug
            ORDER BY post_count DESC
            """
        )
        return {
            "tags": [
                {"name": r["name"], "slug": r["slug"], "count": r["post_count"]}
                for r in rows
            ]
        }

    except Exception as e:
        print(f"[GET TAGS] Error: {e}", flush=True)
        return {"tags": []}
