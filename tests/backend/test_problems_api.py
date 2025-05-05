# tests/backend/test_problems_api.py

from fastapi import status # Import status codes

# Note: The 'client' fixture is automatically available from conftest.py

# --- Test Data (Ensure these match ProblemBase fields) ---
VALID_PROBLEM_DATA_1 = {
    "latex_text": "Solve $x^2 - 4 = 0$.",
    "category": "A", # This is required now in ProblemBase
    "comments": "Simple quadratic equation",
    # "latex_versions": None, # Only include if needed/testing
    # "solution": None,       # Only include if needed/testing
}

VALID_PROBLEM_DATA_2 = {
    "latex_text": "Prove that $\\sqrt{2}$ is irrational.",
    "category": "N", # Required
    "comments": "Proof by contradiction"
}

UPDATE_PROBLEM_DATA = {
    "latex_text": "Solve $x^2 - 9 = 0$.",
    "category": "A", # Required
    "comments": "Updated comment",
}

# --- Test Functions ---

def test_create_problem_success(client):
    response = client.post("/problems/", json=VALID_PROBLEM_DATA_1)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["latex_text"] == VALID_PROBLEM_DATA_1["latex_text"]
    assert data["comments"] == VALID_PROBLEM_DATA_1["comments"]
    assert data["category"] == VALID_PROBLEM_DATA_1["category"]
    assert "id" in data

def test_create_problem_missing_field(client):
    invalid_data = VALID_PROBLEM_DATA_1.copy()
    del invalid_data["latex_text"] # Example: remove a required field
    response = client.post("/problems/", json=invalid_data)
    # FastAPI/Pydantic validation should catch this
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Add more tests for invalid data types if needed

def test_read_all_problems_empty(client):
    response = client.get("/problems/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_read_all_problems_with_data(client):
    # Create a problem first
    client.post("/problems/", json=VALID_PROBLEM_DATA_1)
    client.post("/problems/", json=VALID_PROBLEM_DATA_2)

    response = client.get("/problems/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["latex_text"] == VALID_PROBLEM_DATA_1["latex_text"]
    assert data[1]["latex_text"] == VALID_PROBLEM_DATA_2["latex_text"]

def test_read_problem_not_found(client):
    response = client.get("/problems/999") # Assume 999 doesn't exist
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_read_problem_success(client):
    # Create a problem
    create_response = client.post("/problems/", json=VALID_PROBLEM_DATA_1)
    problem_id = create_response.json()["id"]

    # Read it back
    response = client.get(f"/problems/{problem_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == problem_id
    assert data["latex_text"] == VALID_PROBLEM_DATA_1["latex_text"]
    assert data["category"] == VALID_PROBLEM_DATA_1["category"]

def test_update_problem_not_found(client):
    response = client.put("/problems/999", json=UPDATE_PROBLEM_DATA)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_problem_success(client):
    # Create a problem
    create_response = client.post("/problems/", json=VALID_PROBLEM_DATA_1)
    problem_id = create_response.json()["id"]

    # Update it
    update_response = client.put(f"/problems/{problem_id}", json=UPDATE_PROBLEM_DATA)
    assert update_response.status_code == status.HTTP_200_OK
    updated_data = update_response.json()
    assert updated_data["id"] == problem_id
    assert updated_data["latex_text"] == UPDATE_PROBLEM_DATA["latex_text"]
    assert updated_data["comments"] == UPDATE_PROBLEM_DATA["comments"]
    assert updated_data["category"] == UPDATE_PROBLEM_DATA["category"] # Should remain 'A'

    # Verify by reading again
    get_response = client.get(f"/problems/{problem_id}")
    assert get_response.status_code == status.HTTP_200_OK
    verify_data = get_response.json()
    assert verify_data["latex_text"] == UPDATE_PROBLEM_DATA["latex_text"]
    assert verify_data["comments"] == UPDATE_PROBLEM_DATA["comments"]

def test_delete_problem_not_found(client):
    response = client.delete("/problems/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_problem_success(client):
    # Create a problem
    create_response = client.post("/problems/", json=VALID_PROBLEM_DATA_1)
    problem_id = create_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/problems/{problem_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's gone
    get_response = client.get(f"/problems/{problem_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND