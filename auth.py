from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from config import settings, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
from database import get_db
from utils import get_password_hash, verify_password, create_access_token

router = APIRouter()
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn=Depends(get_db)
) -> str:
    """Verify user is admin"""
    email = await get_current_user(credentials)
    user = await conn.fetchrow("SELECT is_admin FROM users WHERE email = $1", email)
    if not user or not user['is_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")
    return email

@router.post("/register")
async def register(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    conn=Depends(get_db)
):
    """Register new user - accepts Form data"""
    try:
        # Validate inputs
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="Invalid email")
        if not password or len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")

        # Check if user exists
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash password and create user
        hashed = get_password_hash(password)
        user_id = await conn.fetchval(
            "INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id",
            email, hashed, name
        )

        # Create token and return
        token = create_access_token({"sub": email})
        return {
            "access_token": token,
            "user_id": user_id,
            "email": email,
            "name": name,
            "is_admin": False
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    conn=Depends(get_db)
):
    """Login user - accepts Form data"""
    try:
        # Find user
        user = await conn.fetchrow(
            "SELECT id, password_hash, name, is_admin FROM users WHERE email = $1", 
            email
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Verify password
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Create token
        token = create_access_token({"sub": email})
        return {
            "access_token": token,
            "user_id": user["id"],
            "name": user["name"],
            "email": email,
            "is_admin": user["is_admin"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
