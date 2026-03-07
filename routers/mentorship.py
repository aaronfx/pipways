from fastapi import APIRouter, Form, Depends, HTTPException
from typing import Optional
import json
from datetime import datetime

from auth import get_current_user
from database import get_db
from services.analyzer import get_personalized_mentorship as get_mentorship

router = APIRouter()

@router.post("/personalized")
async def get_personalized_mentorship(
    message: str = Form(...),
    context_type: Optional[str] = Form("general"),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Get AI mentorship personalized to user's trading history"""

    user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)

    context = {
        "message": message,
        "type": context_type,
        "timestamp": datetime.utcnow().isoformat()
    }

    mentorship = await get_mentorship(user["id"], context, conn)

    # Save session
    await conn.execute("""
        INSERT INTO mentorship_sessions (user_id, session_type, context, ai_response, resources_suggested)
        VALUES ($1, $2, $3, $4, $5)
    """,
        user["id"],
        context_type,
        json.dumps(context),
        mentorship.get('personalized_response', mentorship.get('response', '')),
        json.dumps(mentorship.get('relevant_resources', []))
    )

    return mentorship

@router.get("/chat")
async def mentor_chat(
    message: str,
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Legacy mentor chat endpoint"""
    return await get_personalized_mentorship(message, "general", current_user, conn)
