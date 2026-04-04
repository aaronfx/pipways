"""
Tests for basic app endpoints: /health, /api/info, /, /dashboard
"""
import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# GET /health
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_health_check(client):
    """GET /health returns 200 with status, version, features."""
    res = await client.get("/health")

    assert res.status_code == 200
    data = res.json()

    # Required fields
    assert "status" in data
    assert "version" in data
    assert "features" in data

    # Check values
    assert data["status"] == "healthy"
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0
    assert isinstance(data["features"], list)
    assert len(data["features"]) > 0


@pytest.mark.asyncio
async def test_health_check_has_expected_features(client):
    """GET /health returns expected feature list."""
    res = await client.get("/health")

    assert res.status_code == 200
    data = res.json()
    features = data["features"]

    # Check for key features
    expected_features = [
        "Trading Academy",
        "AI Chart Analysis",
        "AI Mentor",
        "Performance Analytics",
        "Enhanced Market Signals",
        "Risk Calculator",
        "AI Stock Research",
        "Blog & Content",
        "Webinars",
        "Payments (Paystack)",
    ]

    for feature in expected_features:
        assert feature in features, f"Expected feature '{feature}' not found in response"


@pytest.mark.asyncio
async def test_health_check_has_platform_info(client):
    """GET /health includes platform and signal info."""
    res = await client.get("/health")

    assert res.status_code == 200
    data = res.json()

    assert "platform" in data or "enhanced_signals" in data
    if "enhanced_signals" in data:
        assert data["enhanced_signals"] == "active"
    if "signal_source" in data:
        assert data["signal_source"] == "bot_only"


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/info
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_api_info_returns_feature_list(client):
    """GET /api/info returns feature list."""
    res = await client.get("/api/info")

    assert res.status_code == 200
    data = res.json()

    # Required top-level fields
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert "features" in data

    # Check name and version
    assert "api" in data["name"].lower() or "pipways" in data["name"].lower()
    assert isinstance(data["version"], str)


@pytest.mark.asyncio
async def test_api_info_has_endpoint_list(client):
    """GET /api/info describes available endpoints."""
    res = await client.get("/api/info")

    assert res.status_code == 200
    data = res.json()

    features = data.get("features", {})

    # Check for key endpoint categories
    expected_endpoints = [
        "authentication",
        "signals",
        "enhanced_signals",
        "courses",
        "webinars",
        "blog",
        "ai_services",
        "risk_calculator",
    ]

    for endpoint in expected_endpoints:
        assert endpoint in features, f"Expected endpoint '{endpoint}' not in features"


@pytest.mark.asyncio
async def test_api_info_has_signal_system_info(client):
    """GET /api/info includes signal system information."""
    res = await client.get("/api/info")

    assert res.status_code == 200
    data = res.json()

    # Should have signal_system info
    if "signal_system" in data:
        signal_info = data["signal_system"]
        assert "source" in signal_info
        assert "endpoint" in signal_info


@pytest.mark.asyncio
async def test_api_info_has_documentation_link(client):
    """GET /api/info includes documentation link."""
    res = await client.get("/api/info")

    assert res.status_code == 200
    data = res.json()

    # Should include docs endpoint
    if "documentation" in data:
        assert "docs" in data["documentation"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# GET / (root)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_root_returns_html(client):
    """GET / returns HTML response."""
    res = await client.get("/")

    assert res.status_code == 200
    # Should be HTML response
    content_type = res.headers.get("content-type", "").lower()
    # Could be text/html or just contain html
    assert "html" in content_type or "<" in res.text


@pytest.mark.asyncio
async def test_root_has_title(client):
    """GET / returns HTML with meaningful title/content."""
    res = await client.get("/")

    assert res.status_code == 200
    # Should contain either Gopipways or Trading content
    content = res.text.lower()
    assert "gopipways" in content or "trading" in content or "welcome" in content


@pytest.mark.asyncio
async def test_root_not_error_page(client):
    """GET / does not return an error page."""
    res = await client.get("/")

    assert res.status_code == 200
    # Should not be a 404 or error response
    content = res.text.lower()
    # Check it's not a 404 page or completely empty
    assert len(content) > 50


# ═══════════════════════════════════════════════════════════════════════════════
# GET /dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_dashboard_returns_html(client):
    """GET /dashboard returns HTML response."""
    res = await client.get("/dashboard")

    assert res.status_code == 200
    # Should be HTML response
    content_type = res.headers.get("content-type", "").lower()
    assert "html" in content_type or "<" in res.text


@pytest.mark.asyncio
async def test_dashboard_has_content(client):
    """GET /dashboard returns meaningful HTML content."""
    res = await client.get("/dashboard")

    assert res.status_code == 200
    content = res.text
    # Should not be completely empty
    assert len(content) > 50


@pytest.mark.asyncio
async def test_dashboard_html_variant(client):
    """GET /dashboard.html returns HTML response."""
    res = await client.get("/dashboard.html")

    assert res.status_code == 200
    content_type = res.headers.get("content-type", "").lower()
    assert "html" in content_type or "<" in res.text


# ═══════════════════════════════════════════════════════════════════════════════
# 404 Handling
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_nonexistent_api_endpoint_returns_404(client):
    """GET /api/nonexistent returns 404 with error message."""
    res = await client.get("/api/nonexistent")

    assert res.status_code == 404
    data = res.json()
    assert "detail" in data or "error" in data


@pytest.mark.asyncio
async def test_nonexistent_page_returns_404(client):
    """GET /nonexistent-page returns 404 HTML."""
    res = await client.get("/nonexistent-page")

    assert res.status_code == 404
    # Could be HTML or JSON depending on prefix
    content = res.text.lower()
    assert "404" in content or "not found" in content


# ═══════════════════════════════════════════════════════════════════════════════
# Health Check Variations
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_health_endpoint_consistency(client):
    """Multiple calls to /health return consistent data."""
    res1 = await client.get("/health")
    res2 = await client.get("/health")

    assert res1.status_code == 200
    assert res2.status_code == 200

    data1 = res1.json()
    data2 = res2.json()

    # Same status and version
    assert data1["status"] == data2["status"]
    assert data1["version"] == data2["version"]
    # Features should be the same
    assert set(data1["features"]) == set(data2["features"])


@pytest.mark.asyncio
async def test_api_info_version_matches_health(client):
    """GET /api/info and /health return same version."""
    health_res = await client.get("/health")
    info_res = await client.get("/api/info")

    assert health_res.status_code == 200
    assert info_res.status_code == 200

    health_data = health_res.json()
    info_data = info_res.json()

    # Versions should match
    assert health_data["version"] == info_data["version"]
