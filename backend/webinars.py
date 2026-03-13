"""
Webinars API - PRODUCTION READY
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
from .database import database, webinars_table
from .security import get_current_user

router = APIRouter()

@router.get("/upcoming")
async def get_webinars(upcoming: bool = True, current_user = Depends(get_current_user)):
    """
    Get webinars (upcoming or past)
    PRODUCTION: Real database queries
    """
    try:
        if upcoming:
            query = """
                SELECT * FROM webinars 
                WHERE scheduled_at > NOW() - INTERVAL '2 hours'
                AND status IN ('scheduled', 'live')
                ORDER BY scheduled_at ASC
            """
        else:
            query = """
                SELECT * FROM webinars 
                WHERE status = 'recorded'
                ORDER BY scheduled_at DESC
                LIMIT 10
            """
            
        rows = await database.fetch_all(query)
        
        webinars = []
        for row in rows:
            webinars.append({
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "scheduled_at": row["scheduled_at"].isoformat() if row["scheduled_at"] else None,
                "status": row["status"],  # scheduled, live, recorded
                "duration_minutes": row.get("duration_minutes"),
                "recording_url": row.get("recording_url") if not upcoming else None
            })
            
        return webinars
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch webinars: {e}", flush=True)
        raise HTTPException(500, "Failed to load webinars")
