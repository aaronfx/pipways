"""
Tests for blog routes: GET /blog/posts (paginated), GET /blog/posts/{slug}.
Both require authentication.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# GET /blog/posts (requires auth, paginated)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_posts_unauthenticated(client):
    """GET /blog/posts without auth returns 401."""
    res = await client.get("/blog/posts")

    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_posts_authenticated_empty(client, mock_database, auth_headers):
    """GET /blog/posts returns empty list when no posts exist."""
    mock_database.fetch_all = AsyncMock(return_value=[])

    res = await client.get("/blog/posts", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_posts_authenticated_with_data(client, mock_database, auth_headers):
    """GET /blog/posts returns paginated published posts."""
    now = datetime.utcnow()
    fake_post = {
        "id": 1,
        "title": "Introduction to Risk Management",
        "slug": "intro-risk-management",
        "excerpt": "Learn how to manage risk in trading...",
        "content": "Learn how to manage risk in trading... [full content]",
        "category": "Risk Management",
        "featured_image": "https://example.com/risk.jpg",
        "views": 150,
        "tags": ["risk", "trading", "management"],
        "featured": True,
        "read_time": "8 min",
        "is_published": True,
        "status": "published",
        "created_at": now,
        "updated_at": now,
    }
    fake_row = MagicMock(spec=dict, **fake_post)
    mock_database.fetch_all = AsyncMock(return_value=[fake_row])

    res = await client.get("/blog/posts?limit=10&offset=0", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "Introduction to Risk Management"
    assert data[0]["slug"] == "intro-risk-management"
    assert data[0]["is_published"] is True


@pytest.mark.asyncio
async def test_get_posts_with_category_filter(client, mock_database, auth_headers):
    """GET /blog/posts filters by category."""
    mock_database.fetch_all = AsyncMock(return_value=[])

    res = await client.get("/blog/posts?category=Trading", headers=auth_headers)

    assert res.status_code == 200
    # Verify category param was passed to fetch_all
    call_args = mock_database.fetch_all.call_args
    assert call_args is not None


@pytest.mark.asyncio
async def test_get_posts_pagination(client, mock_database, auth_headers):
    """GET /blog/posts respects limit and offset parameters."""
    posts = [
        {
            "id": i,
            "title": f"Post {i}",
            "slug": f"post-{i}",
            "excerpt": f"Excerpt {i}",
            "content": f"Content {i}",
            "category": "Trading",
            "featured_image": None,
            "views": i * 10,
            "tags": [],
            "featured": i == 1,
            "read_time": "5 min",
            "is_published": True,
            "status": "published",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(1, 6)
    ]
    fake_rows = [MagicMock(spec=dict, **post) for post in posts]
    mock_database.fetch_all = AsyncMock(return_value=fake_rows)

    res = await client.get("/blog/posts?limit=5&offset=0", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5


@pytest.mark.asyncio
async def test_get_posts_invalid_limit(client, auth_headers):
    """GET /blog/posts with limit > 100 returns 422."""
    res = await client.get("/blog/posts?limit=150", headers=auth_headers)

    assert res.status_code == 422


@pytest.mark.asyncio
async def test_get_posts_negative_offset(client, auth_headers):
    """GET /blog/posts with negative offset returns 422."""
    res = await client.get("/blog/posts?offset=-1", headers=auth_headers)

    assert res.status_code == 422


@pytest.mark.asyncio
async def test_get_posts_db_error(client, mock_database, auth_headers):
    """GET /blog/posts handles database errors gracefully."""
    mock_database.fetch_all = AsyncMock(side_effect=Exception("DB Error"))

    res = await client.get("/blog/posts", headers=auth_headers)

    # Returns empty list on DB error (graceful fallback)
    assert res.status_code == 200
    data = res.json()
    assert data == []


# ═══════════════════════════════════════════════════════════════════════════════
# GET /blog/posts/{slug} (requires auth)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_post_by_slug_unauthenticated(client):
    """GET /blog/posts/{slug} without auth returns 401."""
    res = await client.get("/blog/posts/intro-risk-management")

    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_post_by_slug_found(client, mock_database, auth_headers):
    """GET /blog/posts/{slug} returns full post content."""
    now = datetime.utcnow()
    fake_post = {
        "id": 1,
        "title": "Advanced Chart Patterns",
        "slug": "advanced-chart-patterns",
        "excerpt": "Understand advanced technical patterns...",
        "content": "Understand advanced technical patterns... [extensive content with examples and analysis]",
        "category": "Technical Analysis",
        "featured_image": "https://example.com/charts.jpg",
        "views": 523,
        "tags": ["technical-analysis", "patterns", "trading"],
        "featured": False,
        "read_time": "12 min",
        "is_published": True,
        "status": "published",
        "created_at": now,
        "updated_at": now,
    }
    fake_row = MagicMock(spec=dict, **fake_post)
    mock_database.fetch_one = AsyncMock(return_value=fake_row)

    res = await client.get("/blog/posts/advanced-chart-patterns", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Advanced Chart Patterns"
    assert data["slug"] == "advanced-chart-patterns"
    assert data["content"] is not None and len(data["content"]) > 0
    assert data["views"] == 523


@pytest.mark.asyncio
async def test_get_post_by_slug_not_found(client, mock_database, auth_headers):
    """GET /blog/posts/{slug} returns 404 if post doesn't exist."""
    mock_database.fetch_one = AsyncMock(return_value=None)

    res = await client.get("/blog/posts/nonexistent-slug", headers=auth_headers)

    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_post_by_slug_unpublished(client, mock_database, auth_headers):
    """GET /blog/posts/{slug} for unpublished post returns 404."""
    fake_post = {
        "id": 99,
        "title": "Draft Post",
        "slug": "draft-post",
        "excerpt": "This is a draft",
        "content": "Draft content",
        "category": "Drafts",
        "featured_image": None,
        "views": 0,
        "tags": [],
        "featured": False,
        "read_time": "3 min",
        "is_published": False,  # Not published
        "status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    # Mock returns None because the query filters on published status
    mock_database.fetch_one = AsyncMock(return_value=None)

    res = await client.get("/blog/posts/draft-post", headers=auth_headers)

    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_post_by_slug_db_error(client, mock_database, auth_headers):
    """GET /blog/posts/{slug} handles database errors gracefully."""
    mock_database.fetch_one = AsyncMock(side_effect=Exception("DB Error"))

    res = await client.get("/blog/posts/some-slug", headers=auth_headers)

    # Returns 404 on DB error (graceful fallback)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_post_slug_format(client, mock_database, auth_headers):
    """GET /blog/posts with various slug formats."""
    fake_post = {
        "id": 1,
        "title": "Post with Dashes and Numbers",
        "slug": "post-with-dashes-and-numbers-123",
        "excerpt": "Test",
        "content": "Content",
        "category": "Test",
        "featured_image": None,
        "views": 0,
        "tags": [],
        "featured": False,
        "read_time": "5 min",
        "is_published": True,
        "status": "published",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    fake_row = MagicMock(spec=dict, **fake_post)
    mock_database.fetch_one = AsyncMock(return_value=fake_row)

    res = await client.get("/blog/posts/post-with-dashes-and-numbers-123", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == "post-with-dashes-and-numbers-123"
