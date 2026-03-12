from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, insert, update, delete, desc
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import database, courses, users
from .security import get_current_user, get_current_admin

router = APIRouter(prefix="/courses", tags=["courses"])
limiter = Limiter(key_func=get_remote_address)

class CourseCreate(BaseModel):
    title: str
    description: str
    content: str
    category: str
    level: str = Field(..., pattern="^(BEGINNER|INTERMEDIATE|ADVANCED)$")
    price: float = 0.0

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = Field(None, pattern="^(BEGINNER|INTERMEDIATE|ADVANCED)$")
    price: Optional[float] = None
    is_published: Optional[bool] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    content: str
    category: str
    level: str
    price: float
    is_published: bool
    instructor_id: int
    created_at: datetime
    updated_at: datetime

@router.get("/", response_model=List[CourseResponse])
@limiter.limit("30/minute")
async def get_courses(
    request: Request,
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(True),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    query = select(courses).order_by(desc(courses.c.created_at))

    if is_published is not None:
        query = query.where(courses.c.is_published == is_published)
    if category:
        query = query.where(courses.c.category == category)
    if level:
        query = query.where(courses.c.level == level)

    query = query.limit(limit).offset(offset)
    results = await database.fetch_all(query)
    return [dict(row) for row in results]

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int):
    query = select(courses).where(courses.c.id == course_id)
    result = await database.fetch_one(query)
    if not result:
        raise HTTPException(status_code=404, detail="Course not found")
    return dict(result)

@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: dict = Depends(get_current_admin)
):
    query = insert(courses).values(
        title=course_data.title,
        description=course_data.description,
        content=course_data.content,
        category=course_data.category,
        level=course_data.level,
        price=course_data.price,
        is_published=False,
        instructor_id=current_user["id"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    course_id = await database.execute(query)

    query = select(courses).where(courses.c.id == course_id)
    result = await database.fetch_one(query)
    return dict(result)

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_update: CourseUpdate,
    current_user: dict = Depends(get_current_admin)
):
    query = select(courses).where(courses.c.id == course_id)
    existing = await database.fetch_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = course_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    query = update(courses).where(courses.c.id == course_id).values(**update_data)
    await database.execute(query)

    query = select(courses).where(courses.c.id == course_id)
    result = await database.fetch_one(query)
    return dict(result)

@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: dict = Depends(get_current_admin)
):
    query = delete(courses).where(courses.c.id == course_id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}
