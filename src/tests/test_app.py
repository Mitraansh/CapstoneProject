"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participant lists before each test to avoid state leakage."""
    original = {name: {**data, "participants": list(data["participants"])}
                for name, data in activities.items()}
    yield
    for name, data in original.items():
        activities[name]["participants"] = data["participants"]


client = TestClient(app)


def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data


def test_get_activities_has_expected_fields():
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]


def test_signup_invalid_activity():
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_root_redirects():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "/static/index.html" in response.headers["location"]


def test_ask_qualitative_routes_to_rag():
    response = client.post("/api/ask", json={"question": "Tell me about Chess Club"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["source"] == "rag"
    assert "confidence" in data


def test_ask_quantitative_routes_to_text2sql():
    response = client.post(
        "/api/ask", json={"question": "How many students are in Chess Club?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["source"] == "text2sql"
    assert "confidence" in data


def test_ask_unknown_routes_to_direct():
    response = client.post("/api/ask", json={"question": "Hello, can you help me?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["source"] == "direct"
    assert "confidence" in data


def test_ask_missing_question_returns_400():
    response = client.post("/api/ask", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "question field required"


def test_ask_empty_question_returns_400():
    response = client.post("/api/ask", json={"question": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "question field required"
