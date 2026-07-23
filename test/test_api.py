"""Tests for the URL shortener endpoints."""
from fastapi.testclient import TestClient


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "URL Shortener"
    assert data["docs"] == "/docs"


def test_shorten_returns_201_and_valid_payload(client: TestClient):
    response = client.post(
        "/shorten", json={"url": "https://example.com/some/long/path"}
    )
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["code"], str)
    assert len(data["code"]) == 6
    # Pydantic HttpUrl normalizes URLs (may add a trailing slash on bare hosts,
    # but keeps user-provided paths intact).
    assert data["original_url"].startswith("https://example.com/some/long/path")
    assert data["short_url"].endswith(data["code"])
    assert "created_at" in data


def test_shorten_rejects_invalid_url(client: TestClient):
    response = client.post("/shorten", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_shorten_rejects_missing_url(client: TestClient):
    response = client.post("/shorten", json={})
    assert response.status_code == 422


def test_two_shortens_produce_different_codes(client: TestClient):
    r1 = client.post("/shorten", json={"url": "https://example.com/a"})
    r2 = client.post("/shorten", json={"url": "https://example.com/b"})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["code"] != r2.json()["code"]


def test_redirect_returns_302_to_original(client: TestClient):
    create = client.post("/shorten", json={"url": "https://example.com/target"})
    code = create.json()["code"]

    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"].startswith("https://example.com/target")


def test_redirect_unknown_code_returns_404(client: TestClient):
    response = client.get("/abcdef", follow_redirects=False)
    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_stats_for_new_url_shows_zero_clicks(client: TestClient):
    create = client.post("/shorten", json={"url": "https://example.com/x"})
    code = create.json()["code"]

    response = client.get(f"/stats/{code}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == code
    assert data["click_count"] == 0
    assert data["last_clicked_at"] is None
    assert data["top_referrers"] == []
    assert data["top_user_agents"] == []


def test_stats_counts_clicks_and_captures_metadata(client: TestClient):
    create = client.post("/shorten", json={"url": "https://example.com/z"})
    code = create.json()["code"]

    # Three clicks, one with a referer + user-agent, two with just user-agent.
    client.get(
        f"/{code}",
        follow_redirects=False,
        headers={"referer": "https://twitter.com", "user-agent": "TestBot/1.0"},
    )
    client.get(
        f"/{code}",
        follow_redirects=False,
        headers={"user-agent": "TestBot/1.0"},
    )
    client.get(
        f"/{code}",
        follow_redirects=False,
        headers={"user-agent": "OtherBot/2.0"},
    )

    response = client.get(f"/stats/{code}")
    assert response.status_code == 200
    data = response.json()
    assert data["click_count"] == 3
    assert data["last_clicked_at"] is not None

    referrers = {r["value"]: r["count"] for r in data["top_referrers"]}
    assert referrers == {"https://twitter.com": 1}

    user_agents = {r["value"]: r["count"] for r in data["top_user_agents"]}
    assert user_agents == {"TestBot/1.0": 2, "OtherBot/2.0": 1}


def test_stats_unknown_code_returns_404(client: TestClient):
    response = client.get("/stats/nope123")
    assert response.status_code == 404


def test_docs_endpoint_available(client: TestClient):
    """Swagger UI should remain reachable and not be swallowed by /{code}."""
    response = client.get("/docs")
    assert response.status_code == 200
    response = client.get("/openapi.json")
    assert response.status_code == 200
