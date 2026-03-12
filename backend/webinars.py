from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, insert, update, delete, desc
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import database, webinars, users
from .security import get_current_user, get_current_admin

router = APIRouter(prefix="/webinars", tags=["webinars"])
limiter = Limiter(key_func=get_remote_address)

class WebinarCreate(BaseModel):
    title: str
    description: str
    presenter: str
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None

class WebinarUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    presenter: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    meeting_link: Optional[str] = None
    max_participants: Optional[int] = None
    is_recorded: Optional[bool] = None
    recording_url: Optional[str] = None

class WebinarResponse(BaseModel):
    id: int
    title: str
    description: str
    presenter: str
    scheduled_at: datetime
    duration_minutes: int
    meeting_link: Optional[str]
    recording_url: Optional[str]
    max_participants: Optional[int]
    is_recorded: bool
    created_by: int
    created_at: datetime

@router.get("/", response_model=List[WebinarResponse])
@limiter.limit("30/minute")
async def get_webinars(
    request: Request,
    upcoming: bool = Query(True),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    query = select(webinars).order_by(desc(webinars.c.scheduled_at))

    if upcoming:
        query = query.where(webinars.c.scheduled_at > datetime.utcnow())

    query = query.limit(limit).offset(offset)
    results = await database.fetch_all(query)
    return [dict(row) for row in results]

@router.get("/{webinar_id}", response_model=WebinarResponse)
async def get_webinar(webinar_id: int):
    query = select(webinars).where(webinars.c.id == webinar_id)
    result = await database.fetch_one(query)
    if not result:
        raise HTTPException(status_code=404, detail="Webinar not found")
    return dict(result)

@router.post("/", response_model=WebinarResponse)
async def create_webinar(
    webinar_data: WebinarCreate,
    current_user: dict = Depends(get_current_admin)
):
    query = insert(webinars).values(
        title=webinar_data.title,
        description=webinar_data.description,
        presenter=webinar_data.presenter,
        scheduled_at=webinar_data.scheduled_at,
        duration_minutes=webinar_data.duration_minutes,
        meeting_link=webinar_data.meeting_link,
        max_participants=webinar_data.max_participants,
        is_recorded=False,
        created_by=current_user["id"],
        created_at=datetime.utcnow()
    )
    webinar_id = await database.execute(query)

    query = select(webinars).where(webinars.c.id == webinar_id)
    result = await database.fetch_one(query)
    return dict(result)

@router.put("/{webinar_id}", response_model=WebinarResponse)
async def update_webinar(
    webinar_id: int,
    webinar_update: WebinarUpdate,
    current_user: dict = Depends(get_current_admin)
):
    query = select(webinars).where(webinars.c.id == webinar_id)
    existing = await database.fetch_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Webinar not found")

    update_data = webinar_update.dict(exclude_unset=True)
    query = update(webinars).where(webinars.c.id == webinar_id).values(**update_data)
    await database.execute(query)

    query = select(webinars).where(webinars.c.id == webinar_id)
    result = await database.fetch_one(query)
    return dict(result)

@router.delete("/{webinar_id}")
async def delete_webinar(
    webinar_id: int,
    current_user: dict = Depends(get_current_admin)
):
    query = delete(webinars).where(webinars.c.id == webinar_id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Webinar not found")
    return {"message": "Webinar deleted successfully"}
