from pydantic import BaseModel

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        pool = await get_db()
        async with pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            new_access = create_token(
                {"sub": str(user_id), "email": user["email"], "role": user["role"]},
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            new_refresh = create_token(
                {"sub": str(user_id), "type": "refresh"},
                timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )

            return {"access_token": new_access, "refresh_token": new_refresh}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
