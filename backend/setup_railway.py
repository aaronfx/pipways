#!/usr/bin/env python3
"""
Railway Setup Script for Pipways
Run this after the first deployment to set up database tables and seed data.

Usage from Railway shell:
python setup_railway.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.resolve()))

async def main():
    print("🚀 Setting up Pipways on Railway...")
    
    try:
        # Import after path setup
        from backend.database import database, init_database
        
        print("📊 Connecting to database...")
        await init_database()
        print("✅ Database connected successfully")
        
        # Create email and health tables
        try:
            from backend.email_service import ensure_email_tables
            await ensure_email_tables()
            print("✅ Email tables created")
        except Exception as e:
            print(f"⚠️  Email tables warning: {e}")
        
        try:
            from backend.health_check import ensure_health_tables
            await ensure_health_tables()
            print("✅ Health check tables created")
        except Exception as e:
            print(f"⚠️  Health check tables warning: {e}")
        
        # Initialize LMS (Academy) if available
        try:
            from backend.lms_init import init_lms_tables
            print("📚 Setting up Academy curriculum...")
            await init_lms_tables()
            print("✅ Academy curriculum initialized")
        except Exception as e:
            print(f"⚠️  LMS setup warning: {e}")
        
        # Set up subscriptions
        try:
            from backend.subscriptions import init_subscription_tables
            await init_subscription_tables()
            print("✅ Subscription tables created")
        except Exception as e:
            print(f"⚠️  Subscription tables warning: {e}")
        
        # Set up CMS settings
        try:
            import backend.cms as cms
            await cms._ensure_settings_table()
            print("✅ CMS settings table ready")
        except Exception as e:
            print(f"⚠️  CMS settings warning: {e}")
        
        # Seed blog posts
        try:
            from backend.blog_enhanced import seed_initial_posts
            await seed_initial_posts()
            print("✅ Blog posts seeded")
        except Exception as e:
            print(f"⚠️  Blog seeding warning: {e}")
        
        print("\n🎉 Pipways setup complete!")
        print("\n📋 Next steps:")
        print("1. Visit your Railway app URL")
        print("2. Click 'Sign Up' to create your admin account")
        print("3. The first user becomes admin automatically")
        print("4. Test the /health endpoint to verify everything works")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        try:
            await database.disconnect()
            print("🔌 Database connection closed")
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
