from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_categorize_endpoint_success():
    payload = {"input_text": "Booked a flight ticket"}
    response = client.post("/api/categorize", json=payload, params={"user_id": "test_user"})

    assert response.status_code == 200
    data = response.json()

    assert "category" in data
    assert "reasoning" in data
    assert isinstance(data["category"], str)

def test_categorize_endpoint_empty_text():
    payload = {"input_text": ""}
    response = client.post("/api/categorize", json=payload, params={"user_id": "test_user"})

    assert response.status_code == 200  # You may return 400 if validation added
    data = response.json()
    assert data["category"] in ["Unknown", ""]  # Depends on fallback logic
