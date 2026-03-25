"""
Add permanent featured images to the two SEO blog posts.
Uses free Unsplash images that never expire or go 404.

Run from Render Shell:
    python -m backend.add_blog_images
"""

import os
import asyncio
from databases import Database

DATABASE_URL = os.getenv("DATABASE_URL", "")

IMAGES = {
    "forex-position-size-calculator-nigeria": {
        "featured_image": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&q=80",
        # Photo: trading charts on monitor — free Unsplash
    },
    "learn-forex-trading-nigeria-free-beginners-guide": {
        "featured_image": "https://images.unsplash.com/photo-1642790106117-e829e14a795f?w=1200&q=80",
        # Photo: person studying financial charts — free Unsplash
    },
}


async def run():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set")
        return

    url = DATABASE_URL
    if "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")

    db = Database(url)
    await db.connect()

    for slug, data in IMAGES.items():
        try:
            await db.execute(
                "UPDATE blog_posts SET featured_image = :img WHERE slug = :slug",
                {"img": data["featured_image"], "slug": slug}
            )
            print(f"✅ Updated: {slug}")
        except Exception as e:
            print(f"❌ Failed {slug}: {e}")

    await db.disconnect()
    print("\nDone. Images now use permanent Unsplash URLs.")
    print("You can change these anytime in CMS → Blog → Edit Post → Featured Image")


if __name__ == "__main__":
    asyncio.run(run())
