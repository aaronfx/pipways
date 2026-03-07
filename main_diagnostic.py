"""
Pipways Diagnostic - Minimal version to check deployment
"""

import os
import asyncpg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "")

@app.get("/")
async def root():
    return {"status": "API is running", "version": "diagnostic"}

@app.get("/health")
async def health():
    return {"status": "ok", "database_url_set": bool(DATABASE_URL)}

@app.get("/check-db")
async def check_db():
    """Check database connection and admin user"""
    if not DATABASE_URL:
        return {"error": "DATABASE_URL not set"}

    try:
        conn = await asyncpg.connect(DATABASE_URL, ssl="require")

        # Check if users table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)

        if not table_exists:
            return {"error": "Users table does not exist"}

        # Check admin user
        admin = await conn.fetchrow(
            "SELECT id, email, is_admin FROM users WHERE email = 'admin@pipways.com'"
        )

        await conn.close()

        if admin:
            return {
                "status": "ok",
                "admin_exists": True,
                "admin_email": admin["email"],
                "is_admin": admin["is_admin"]
            }
        else:
            return {
                "status": "ok",
                "admin_exists": False,
                "message": "Admin user not found"
            }

    except Exception as e:
        return {"error": str(e)}

@app.get("/create-admin")
async def create_admin():
    """Create admin user if missing"""
    if not DATABASE_URL:
        return {"error": "DATABASE_URL not set"}

    try:
        import bcrypt
        conn = await asyncpg.connect(DATABASE_URL, ssl="require")

        # Create users table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100),
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check if admin exists
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = 'admin@pipways.com'"
        )

        if existing:
            await conn.close()
            return {"message": "Admin already exists"}

        # Create admin
        password = "admin123"
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

        await conn.execute(
            "INSERT INTO users (email, password_hash, name, is_admin) VALUES ($1, $2, $3, $4)",
            "admin@pipways.com", hashed, "Admin", True
        )

        await conn.close()
        return {"message": "Admin created successfully"}

    except Exception as e:
        return {"error": str(e)}
