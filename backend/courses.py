@router.post("")
async def create_course(course: CourseCreate, current_user: dict = Depends(get_admin_user)):
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            INSERT INTO courses (title, description, content, level, duration_hours, thumbnail, is_premium, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
        """
        course_id = await conn.fetchval(
            query,
            course.title,
            course.description,
            course.content,
            course.level,
            course.duration_hours,
            course.thumbnail,
            course.is_premium,
            current_user["id"]
        )
        return {"id": course_id, "message": "Course created successfully"}
