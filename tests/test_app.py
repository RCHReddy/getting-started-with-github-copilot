import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy

# Create a deep copy of the original activities for resetting between tests
original_activities = copy.deepcopy(activities)

@pytest.fixture
def client():
    # Reset the global activities dictionary before each test
    global activities
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    return TestClient(app)

def test_root_redirect(client):
    """Test that the root endpoint redirects to the static index.html"""
    # Arrange - No special setup needed

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"

def test_get_activities(client):
    """Test getting all activities returns the correct structure"""
    # Arrange - No special setup needed

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # Based on the initial activities

    # Check that a known activity has the expected structure
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)

def test_signup_success(client):
    """Test successful signup for an activity"""
    # Arrange
    initial_participants = len(activities["Chess Club"]["participants"])

    # Act
    response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Signed up newstudent@mergington.edu for Chess Club" == data["message"]

    # Verify the participant was added
    assert len(activities["Chess Club"]["participants"]) == initial_participants + 1
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

def test_signup_activity_not_found(client):
    """Test signup fails when activity does not exist"""
    # Arrange - No special setup needed

    # Act
    response = client.post("/activities/Nonexistent Activity/signup?email=test@mergington.edu")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Activity not found"

def test_signup_already_signed_up(client):
    """Test signup fails when student is already signed up"""
    # Arrange
    # First signup
    client.post("/activities/Programming Class/signup?email=duplicate@mergington.edu")

    # Act
    # Attempt duplicate signup
    response = client.post("/activities/Programming Class/signup?email=duplicate@mergington.edu")

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Student already signed up for this activity"

def test_remove_participant_success(client):
    """Test successful removal of a participant"""
    # Arrange
    initial_participants = len(activities["Chess Club"]["participants"])
    existing_email = activities["Chess Club"]["participants"][0]  # michael@mergington.edu

    # Act
    response = client.delete(f"/activities/Chess Club/participants?email={existing_email}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert f"Removed {existing_email} from Chess Club" == data["message"]

    # Verify the participant was removed
    assert len(activities["Chess Club"]["participants"]) == initial_participants - 1
    assert existing_email not in activities["Chess Club"]["participants"]

def test_remove_participant_activity_not_found(client):
    """Test removal fails when activity does not exist"""
    # Arrange - No special setup needed

    # Act
    response = client.delete("/activities/Nonexistent Activity/participants?email=test@mergington.edu")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Activity not found"

def test_remove_participant_not_found(client):
    """Test removal fails when participant is not signed up"""
    # Arrange - No special setup needed

    # Act
    response = client.delete("/activities/Chess Club/participants?email=notsignedup@mergington.edu")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Participant not found"

def test_signup_multiple_activities(client):
    """Test that a student can sign up for multiple activities"""
    # Arrange
    email = "multiactivity@mergington.edu"

    # Act
    # Sign up for two different activities
    response1 = client.post("/activities/Chess Club/signup?email=" + email)
    response2 = client.post("/activities/Programming Class/signup?email=" + email)

    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200

    # Verify signed up for both
    assert email in activities["Chess Club"]["participants"]
    assert email in activities["Programming Class"]["participants"]

def test_remove_participant_case_sensitivity(client):
    """Test that email matching is case-sensitive"""
    # Arrange
    # Add a participant with mixed case
    email_mixed = "TestCase@mergington.edu"
    client.post("/activities/Gym Class/signup?email=" + email_mixed)

    # Act
    # Try to remove with different case
    response = client.delete("/activities/Gym Class/participants?email=testcase@mergington.edu")

    # Assert
    assert response.status_code == 404  # Should not find due to case difference

    # Verify still in participants
    assert email_mixed in activities["Gym Class"]["participants"]