"""
Fix: Clear broken featured_image URLs from blog posts.

Render's filesystem resets on every deploy, so images uploaded via CMS
to /static/uploads/ are lost. This script clears those broken URLs so
the blog shows clean gradient placeholders instead of 404 errors.

Run from Render Shell:
    python -m backend.fix_blog_images

After running, add featured images via external URLs (Unsplash, Cloudinary etc)
or upload to a persistent storage service like Cloudinary or AWS S3.
"""

import os
import asyncio
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "")


async def fix():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set")
        return

    url = DATABASE_URL
    if "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")

    db = Database(url)
    await db.connect()

    # Find all posts with local upload paths
    rows = await db.fetch_all(
        "SELECT id, title, featured_image FROM blog_posts "
        "WHERE featured_image LIKE '/static/uploads/%' "
        "OR featured_image LIKE 'static/uploads/%'"
    )

    if not rows:
        print("✅ No broken image URLs found.")
        await db.disconnect()
        return

    print(f"Found {len(rows)} posts with local upload paths:")
    for row in rows:
        print(f"  - [{row['id']}] {row['title'][:50]} → {row['featured_image'][:60]}")

    # Clear them
    result = await db.execute(
        "UPDATE blog_posts SET featured_image = '' "
        "WHERE featured_image LIKE '/static/uploads/%' "
        "OR featured_image LIKE 'static/uploads/%'"
    )

    print(f"\n✅ Cleared {len(rows)} broken image URLs.")
    print("\nTo add featured images that persist across deploys, use external URLs:")
    print("  • Unsplash: https://images.unsplash.com/photo-...")
    print("  • Cloudinary: https://res.cloudinary.com/...")
    print("  • Any public image URL works in the CMS featured_image field.")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(fix())
