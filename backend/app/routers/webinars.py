
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.dependencies import get_current_user
from app.config import settings
import asyncpg

router = APIRouter(prefix="/webinars", tags=["webinars"])

async def get_db():
    return await asyncpg.create_pool(settings.DATABASE_URL)

@router.get("/")
async def get_webinars(limit: int = 20, current_user: dict = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        webinars = await conn.fetch("""
            SELECT w.*, u.full_name as host_name,
                   (SELECT COUNT(*) FROM webinar_registrations WHERE webinar_id = w.id) as registration_count
            FROM webinars w
            JOIN users u ON w.host_id = u.id
            WHERE w.scheduled_at > NOW() 
            AND (w.is_premium = false OR $1 = true)
            ORDER BY w.scheduled_at ASC
            LIMIT $2
        """, current_user.get("subscription_tier") in ["premium", "pro"], limit)

        return {"webinars": [dict(w) for w in webinars]}

@router.post("/{webinar_id}/register")
async def register_webinar(webinar_id: int, current_user: dict = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        # Check if exists
        existing = await conn.fetchval("""
            SELECT id FROM webinar_registrations 
            WHERE webinar_id = $1 AND user_id = $2
        """, webinar_id, current_user["id"])

        if existing:
            raise HTTPException(status_code=400, detail="Already registered")

        await conn.execute("""
            INSERT INTO webinar_registrations (webinar_id, user_id, registered_at)
            VALUES ($1, $2, $3)
        """, webinar_id, current_user["id"], datetime.utcnow())

        return {"message": "Registered successfully"}
