import asyncpg
from config import settings, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD

async def get_db():
    """Database dependency for FastAPI"""
    conn = await asyncpg.connect(settings.DATABASE_URL, ssl="require")
    try:
        yield conn
    finally:
        await conn.close()

async def init_db():
    """Initialize database tables and default admin"""
    conn = await asyncpg.connect(settings.DATABASE_URL, ssl="require")

    try:
        # Users table
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

        # Trades table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                pair VARCHAR(10) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                entry_price DECIMAL(10,5),
                exit_price DECIMAL(10,5),
                pips INTEGER,
                grade VARCHAR(5),
                screenshot_url TEXT,
                ai_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Chart analyses table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chart_analyses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                image_data TEXT,
                analysis_result JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Blog posts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                slug VARCHAR(255) UNIQUE NOT NULL,
                content TEXT NOT NULL,
                excerpt TEXT,
                featured_image TEXT,
                meta_title VARCHAR(70),
                meta_description VARCHAR(160),
                meta_keywords TEXT,
                author_id INTEGER REFERENCES users(id),
                category VARCHAR(100),
                tags TEXT[],
                status VARCHAR(20) DEFAULT 'draft',
                published_at TIMESTAMP,
                view_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Blog categories table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                meta_title VARCHAR(70),
                meta_description VARCHAR(160),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Media uploads table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                original_name VARCHAR(255) NOT NULL,
                file_path TEXT NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(100),
                alt_text VARCHAR(255),
                uploaded_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Trade analysis uploads table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_analysis_uploads (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_data TEXT,
                extracted_data JSONB,
                analysis_result JSONB,
                trader_type VARCHAR(50),
                trader_score INTEGER,
                mistakes_detected JSONB,
                patterns_detected JSONB,
                recommendations TEXT[],
                learning_resources TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Mentorship sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mentorship_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                session_type VARCHAR(50),
                context JSONB,
                ai_response TEXT,
                resources_suggested JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create default admin user
        from auth import get_password_hash
        existing_admin = await conn.fetchrow(
            "SELECT id, is_admin FROM users WHERE email = $1", 
            DEFAULT_ADMIN_EMAIL
        )

        if not existing_admin:
            hashed = get_password_hash(DEFAULT_ADMIN_PASSWORD)
            await conn.execute(
                """INSERT INTO users (email, password_hash, name, is_admin) 
                   VALUES ($1, $2, $3, $4)""",
                DEFAULT_ADMIN_EMAIL, hashed, "Admin", True
            )
            print(f"✅ Default admin created: {DEFAULT_ADMIN_EMAIL}")
        else:
            # Ensure admin has privileges
            await conn.execute(
                "UPDATE users SET is_admin = TRUE WHERE email = $1",
                DEFAULT_ADMIN_EMAIL
            )
            print(f"✅ Admin verified: {DEFAULT_ADMIN_EMAIL}")

    finally:
        await conn.close()
