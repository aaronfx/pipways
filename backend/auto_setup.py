"""
Auto Database Setup for Railway
This script runs automatically when the app starts if tables don't exist.
"""

import asyncio
import os
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.resolve()))

async def auto_setup_if_needed():
    """Check if database is empty and set it up automatically."""
    try:
        from backend.database import database
        
        # Check if users table exists (basic check for setup completion)
        try:
            result = await database.fetch_one("SELECT COUNT(*) as count FROM users LIMIT 1")
            if result and result['count'] >= 0:
                print("[AUTO-SETUP] Database already initialized, skipping setup", flush=True)
                return
        except Exception:
            # Table doesn't exist, need to set up
            pass
        
        print("[AUTO-SETUP] Empty database detected, running automatic setup...", flush=True)
        
        # Run basic table creation
        from backend.database import init_database, run_migrations
        await init_database()
        await run_migrations()
        
        # Initialize LMS
        try:
            from backend.lms_init import init_lms_tables
            await init_lms_tables()
            print("[AUTO-SETUP] ✅ Academy initialized", flush=True)
        except Exception as e:
            print(f"[AUTO-SETUP] ⚠️  Academy setup warning: {e}", flush=True)
        
        # Initialize subscription tables
        try:
            from backend.subscriptions import init_subscription_tables
            await init_subscription_tables()
            print("[AUTO-SETUP] ✅ Subscription system ready", flush=True)
        except Exception as e:
            print(f"[AUTO-SETUP] ⚠️  Subscription setup warning: {e}", flush=True)
        
        # Initialize email tables
        try:
            from backend.email_service import ensure_email_tables
            await ensure_email_tables()
            print("[AUTO-SETUP] ✅ Email system ready", flush=True)
        except Exception as e:
            print(f"[AUTO-SETUP] ⚠️  Email setup warning: {e}", flush=True)
        
        # Initialize health check tables
        try:
            from backend.health_check import ensure_health_tables
            await ensure_health_tables()
            print("[AUTO-SETUP] ✅ Health monitoring ready", flush=True)
        except Exception as e:
            print(f"[AUTO-SETUP] ⚠️  Health setup warning: {e}", flush=True)
        
        # Initialize CMS
        try:
            import backend.cms as cms
            await cms._ensure_settings_table()
            print("[AUTO-SETUP] ✅ CMS ready", flush=True)
        except Exception as e:
            print(f"[AUTO-SETUP] ⚠️  CMS setup warning: {e}", flush=True)
        
        print("[AUTO-SETUP] 🎉 Automatic setup complete! First user to register becomes admin.", flush=True)
        
    except Exception as e:
        print(f"[AUTO-SETUP] ❌ Setup failed: {e}", flush=True)
        # Don't raise - let app start anyway
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(auto_setup_if_needed())
