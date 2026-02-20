from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# -----------------------------
# Health Check
# -----------------------------
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


# -----------------------------
# CRM Query Test
# -----------------------------
def test_crm_query_voice():
    payload = {
        "source": "crm",
        "mode": "voice",
        "filters": {"status": "active"},
        "limit": 5,
    }

    response = client.post("/query", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["source"] == "crm"
    assert data["mode"] == "voice"
    assert "items" in data
    assert "freshness" in data
    assert data["page"]["returned"] <= 5


# -----------------------------
# Support Query Test
# -----------------------------
def test_support_query():
    payload = {
        "source": "support",
        "mode": "voice",
        "filters": {"status": "open"},
        "limit": 5,
    }

    response = client.post("/query", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["source"] == "support"
    assert data["data_type"] == "tabular_support"


# -----------------------------
# Analytics Query Test
# -----------------------------
def test_analytics_query():
    payload = {
        "source": "analytics",
        "mode": "voice",
        "filters": {"metric": "daily_active_users"},
        "limit": 3,
    }

    response = client.post("/query", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["source"] == "analytics"
    assert data["data_type"] == "time_series"
    assert len(data["items"]) <= 3


# -----------------------------
# Pagination Test
# -----------------------------
def test_pagination():
    first_page = client.post(
        "/query",
        json={
            "source": "crm",
            "mode": "voice",
            "limit": 5,
        },
    )

    assert first_page.status_code == 200
    first_data = first_page.json()

    next_cursor = first_data["page"]["next_cursor"]
    assert next_cursor is not None

    second_page = client.post(
        "/query",
        json={
            "source": "crm",
            "mode": "voice",
            "limit": 5,
            "cursor": next_cursor,
        },
    )

    assert second_page.status_code == 200
    second_data = second_page.json()

    assert second_data["page"]["returned"] <= 5
