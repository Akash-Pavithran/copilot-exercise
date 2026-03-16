import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_get_activities():
    """Test retrieving all activities"""
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0

    # Check structure of first activity
    first_activity = next(iter(data.values()))
    required_keys = ["description", "schedule", "max_participants", "participants"]
    for key in required_keys:
        assert key in first_activity

    assert isinstance(first_activity["participants"], list)


def test_signup_success():
    """Test successful signup for an activity"""
    response = client.post("/activities/Chess%20Club/signup?email=newstudent@mergington.edu")
    assert response.status_code == 200

    result = response.json()
    assert "message" in result
    assert "Signed up newstudent@mergington.edu for Chess Club" == result["message"]


def test_signup_duplicate():
    """Test preventing duplicate signup"""
    email = "duplicatetest@mergington.edu"

    # First signup should succeed
    response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert response1.status_code == 200

    # Second signup should fail
    response2 = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert response2.status_code == 400

    result = response2.json()
    assert "detail" in result
    assert "already signed up" in result["detail"]


def test_signup_activity_not_found():
    """Test signup for non-existent activity"""
    response = client.post("/activities/NonExistent/signup?email=test@mergington.edu")
    assert response.status_code == 404

    result = response.json()
    assert "detail" in result
    assert "Activity not found" in result["detail"]


def test_signup_max_participants_exceeded():
    """Test signup when max participants would be exceeded"""
    # Note: Current implementation doesn't check max_participants
    # This test documents that it currently allows exceeding the limit
    activity = "Chess Club"
    max_participants = 12  # From the data

    # Get current count
    response = client.get("/activities")
    data = response.json()
    current_count = len(data[activity]["participants"])

    # Add participants until we exceed max
    for i in range(max_participants - current_count + 2):  # +2 to exceed
        email = f"overflow{i}@mergington.edu"
        response = client.post(f"/activities/{activity}/signup?email={email}")
        # Currently, this succeeds even when exceeding max_participants
        assert response.status_code == 200


def test_unregister_success():
    """Test successful unregistration from an activity"""
    email = "unregistertest@mergington.edu"
    activity = "Programming Class"

    # First signup
    client.post(f"/activities/{activity}/signup?email={email}")

    # Then unregister
    response = client.delete(f"/activities/{activity}/participants/{email}")
    assert response.status_code == 200

    result = response.json()
    assert "message" in result
    assert f"Unregistered {email} from {activity}" == result["message"]


def test_unregister_not_registered():
    """Test unregistering a student not signed up"""
    email = "notregistered@mergington.edu"
    activity = "Programming Class"

    response = client.delete(f"/activities/{activity}/participants/{email}")
    assert response.status_code == 400

    result = response.json()
    assert "detail" in result
    assert "not registered" in result["detail"]


def test_unregister_activity_not_found():
    """Test unregistering from non-existent activity"""
    response = client.delete("/activities/NonExistent/participants/test@mergington.edu")
    assert response.status_code == 404

    result = response.json()
    assert "detail" in result
    assert "Activity not found" in result["detail"]


def test_root_redirect():
    """Test root endpoint redirects to static index"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect

    assert response.headers["location"] == "/static/index.html"