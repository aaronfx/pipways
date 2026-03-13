"""
Database migration script to add missing columns.
Run this once to fix the schema: python backend/migrate.py
"""
import os
import asyncio
from sqlalchemy import create_engine, text
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/pipways")

def run_migration():
    """Add missing columns to users table."""
    # Use sync connection for ALTER TABLE
    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    
    with engine.connect() as conn:
        print("Checking database schema...")
        
        # Check existing columns
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'users'
        """))
        existing_cols = [row[0] for row in result]
        print(f"Existing columns: {existing_cols}")
        
        # Add missing columns
        migrations = [
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("is_admin", "BOOLEAN DEFAULT FALSE"),
            ("role", "VARCHAR(50) DEFAULT 'user'"),
            ("subscription_tier", "VARCHAR(50) DEFAULT 'free'"),
            ("full_name", "VARCHAR(255) DEFAULT ''")
        ]
        
        for col_name, col_type in migrations:
            if col_name not in existing_cols:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✓ Added column: {col_name}")
                except Exception as e:
                    print(f"⚠ Error adding {col_name}: {e}")
            else:
                print(f"✓ Column already exists: {col_name}")
        
        print("Migration complete!")

if __name__ == "__main__":
    run_migration()
