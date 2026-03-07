import asyncpg
from config import settings, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
from utils import get_password_hash

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
                author_id INTEGER REFERENCES users(id),
                category VARCHAR(100),
                tags TEXT[],
                status VARCHAR(20) DEFAULT 'draft',
                published_at TIMESTAMP,
                view_count INTEGER DEFAULT 0,
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
                analysis_result JSONB,
                trader_type VARCHAR(50),
                trader_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create default admin user (Fix #4)
        admin = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1",
            DEFAULT_ADMIN_EMAIL
        )

        if not admin:
            hashed = get_password_hash(DEFAULT_ADMIN_PASSWORD)
            await conn.execute(
                """
                INSERT INTO users (email, password_hash, name, is_admin)
                VALUES ($1, $2, 'Administrator', TRUE)
                """,
                DEFAULT_ADMIN_EMAIL,
                hashed
            )
            print(f"✅ Default admin created: {DEFAULT_ADMIN_EMAIL}")
        else:
            print(f"✅ Admin already exists: {DEFAULT_ADMIN_EMAIL}")

    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise
    finally:
        await conn.close()
