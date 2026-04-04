"""
One-time migration: fix broken /static/uploads/ URLs in the database.

Railway's filesystem resets on every deploy, so images stored at /static/uploads/
are lost. The media.py module serves files from PostgreSQL at /cms/media/serve/.

This script:
  1. Finds all blog_posts, webinars, and media_library rows referencing /static/uploads/
  2. Checks if the file exists in the media_files table (PostgreSQL-backed)
  3. Updates the URL to /cms/media/serve/ if the file is found in DB
  4. Clears the URL if the file isn't in DB (avoids broken image references)

Run from Railway shell:
    python -m backend.fix_media_urls
"""
import asyncio
import os
import sys

# Ensure the parent directory is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import database, DATABASE_URL


async def fix_urls():
    await database.connect()
    print("[FIX MEDIA] Connected to database")

    fixed = 0

    # ── Blog posts: featured_image and og_image_url ──────────────────────────
    for col in ("featured_image", "og_image_url"):
        try:
            rows = await database.fetch_all(
                f"SELECT id, {col} FROM blog_posts "
                f"WHERE {col} LIKE '/static/uploads/%'"
            )
            for row in rows:
                old_url = row[col]
                # Extract the filename part: /static/uploads/general/abc.jpg -> general/abc.jpg
                filename = old_url.replace("/static/uploads/", "")
                # Check if file exists in media_files
                found = await database.fetch_one(
                    "SELECT url FROM media_files WHERE filename = :fn",
                    {"fn": filename}
                )
                if found:
                    new_url = found["url"]
                else:
                    new_url = ""  # Clear broken reference
                await database.execute(
                    f"UPDATE blog_posts SET {col} = :url WHERE id = :id",
                    {"url": new_url, "id": row["id"]}
                )
                print(f"  blog_posts.{col} id={row['id']}: {old_url} -> {new_url or '(cleared)'}")
                fixed += 1
        except Exception as e:
            print(f"  blog_posts.{col} skip: {e}")

    # ── Webinars: thumbnail ──────────────────────────────────────────────────
    try:
        rows = await database.fetch_all(
            "SELECT id, thumbnail FROM webinars "
            "WHERE thumbnail LIKE '/static/uploads/%'"
        )
        for row in rows:
            old_url = row["thumbnail"]
            filename = old_url.replace("/static/uploads/", "")
            found = await database.fetch_one(
                "SELECT url FROM media_files WHERE filename = :fn",
                {"fn": filename}
            )
            new_url = found["url"] if found else ""
            await database.execute(
                "UPDATE webinars SET thumbnail = :url WHERE id = :id",
                {"url": new_url, "id": row["id"]}
            )
            print(f"  webinars.thumbnail id={row['id']}: {old_url} -> {new_url or '(cleared)'}")
            fixed += 1
    except Exception as e:
        print(f"  webinars.thumbnail skip: {e}")

    # ── media_library: url ───────────────────────────────────────────────────
    try:
        rows = await database.fetch_all(
            "SELECT id, filename, url FROM media_library "
            "WHERE url LIKE '/static/uploads/%'"
        )
        for row in rows:
            new_url = f"/cms/media/serve/{row['filename']}"
            await database.execute(
                "UPDATE media_library SET url = :url WHERE id = :id",
                {"url": new_url, "id": row["id"]}
            )
            print(f"  media_library id={row['id']}: {row['url']} -> {new_url}")
            fixed += 1
    except Exception as e:
        print(f"  media_library skip: {e}")

    await database.disconnect()
    print(f"\n[FIX MEDIA] Done — {fixed} URLs updated")


if __name__ == "__main__":
    asyncio.run(fix_urls())
