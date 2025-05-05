# tests/backend/test_problemsets_api.py

import pytest # Keep pytest import if needed for specific markers later
from fastapi import status # Import status codes

# Note: The 'client' and 'test_db' fixtures are automatically available from conftest.py

# --- Test Data (Matching ProblemsetCreate/Update) ---
VALID_PROBLEMSET_DATA_1 = {
    "title": "Ljetni Kamp Algebra 1",
    "type": "predavanje",
    "part_of": "ljetni kamp",
    "group_name": "pocetna"
}

VALID_PROBLEMSET_DATA_2 = {
    "title": "Skola Mate Kombinatorika Vjezbe",
    "type": "vjezbe",
    "part_of": "skola matematike",
    "group_name": "napredna"
}

UPDATE_PROBLEMSET_DATA = {
    "title": "Ljetni Kamp Algebra 1 - Updated",
    "type": "predavanje-updated", # Changed type
    "part_of": "ljetni kamp 2024", # Changed context
    "group_name": "pocetna-revised" # Changed group
}

INVALID_PROBLEMSET_DATA_MISSING_FIELD = {
    # Missing 'title' which is required
    "type": "predavanje",
    "part_of": "ljetni kamp",
    "group_name": "pocetna"
}

# --- NEW CRUD Test Functions ---

def test_create_problemset_success(client):
    response = client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_1)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == VALID_PROBLEMSET_DATA_1["title"]
    assert data["type"] == VALID_PROBLEMSET_DATA_1["type"]
    assert data["part_of"] == VALID_PROBLEMSET_DATA_1["part_of"]
    assert data["group_name"] == VALID_PROBLEMSET_DATA_1["group_name"]
    assert "id" in data
    assert "problems" in data # Should be an empty list by default on creation
    assert isinstance(data["problems"], list)

def test_create_problemset_missing_required_field(client):
    response = client.post("/problemsets/", json=INVALID_PROBLEMSET_DATA_MISSING_FIELD)
    # FastAPI/Pydantic validation should catch this
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Test creating with optional field missing (should work)
def test_create_problemset_optional_field_missing(client):
    data_no_group = VALID_PROBLEMSET_DATA_1.copy()
    del data_no_group["group_name"]
    response = client.post("/problemsets/", json=data_no_group)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == data_no_group["title"]
    assert data["group_name"] is None # Check it defaults to None or the DB default

def test_read_all_problemsets_empty(client):
    response = client.get("/problemsets/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_read_all_problemsets_with_data(client):
    # Create a couple of problemsets
    client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_1)
    client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_2)

    response = client.get("/problemsets/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    # Check titles to ensure different items were returned (order might vary)
    titles = {item["title"] for item in data}
    assert VALID_PROBLEMSET_DATA_1["title"] in titles
    assert VALID_PROBLEMSET_DATA_2["title"] in titles

def test_read_problemset_not_found(client):
    response = client.get("/problemsets/999") # Assume 999 doesn't exist
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_read_problemset_success(client):
    # Create a problemset
    create_response = client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_1)
    assert create_response.status_code == status.HTTP_201_CREATED
    problemset_id = create_response.json()["id"]

    # Read it back
    response = client.get(f"/problemsets/{problemset_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == problemset_id
    assert data["title"] == VALID_PROBLEMSET_DATA_1["title"]
    assert data["type"] == VALID_PROBLEMSET_DATA_1["type"]
    assert data["group_name"] == VALID_PROBLEMSET_DATA_1["group_name"]
    # Add checks for other fields as needed

def test_update_problemset_not_found(client):
    response = client.put("/problemsets/999", json=UPDATE_PROBLEMSET_DATA)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_problemset_success(client):
    # Create a problemset
    create_response = client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_1)
    assert create_response.status_code == status.HTTP_201_CREATED
    problemset_id = create_response.json()["id"]

    # Update it
    update_response = client.put(f"/problemsets/{problemset_id}", json=UPDATE_PROBLEMSET_DATA)
    assert update_response.status_code == status.HTTP_200_OK
    updated_data = update_response.json()
    assert updated_data["id"] == problemset_id
    assert updated_data["title"] == UPDATE_PROBLEMSET_DATA["title"]
    assert updated_data["type"] == UPDATE_PROBLEMSET_DATA["type"]
    assert updated_data["part_of"] == UPDATE_PROBLEMSET_DATA["part_of"]
    assert updated_data["group_name"] == UPDATE_PROBLEMSET_DATA["group_name"]

    # Verify by reading again
    get_response = client.get(f"/problemsets/{problemset_id}")
    assert get_response.status_code == status.HTTP_200_OK
    verify_data = get_response.json()
    assert verify_data["title"] == UPDATE_PROBLEMSET_DATA["title"]
    assert verify_data["type"] == UPDATE_PROBLEMSET_DATA["type"]

def test_update_problemset_invalid_data(client):
    # Create a problemset
    create_response = client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_1)
    assert create_response.status_code == status.HTTP_201_CREATED
    problemset_id = create_response.json()["id"]

    # Attempt update with missing required field
    invalid_update_data = UPDATE_PROBLEMSET_DATA.copy()
    del invalid_update_data["title"]
    update_response = client.put(f"/problemsets/{problemset_id}", json=invalid_update_data)
    assert update_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_problemset_not_found(client):
    response = client.delete("/problemsets/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_problemset_success(client):
    # Create a problemset
    create_response = client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_1)
    assert create_response.status_code == status.HTTP_201_CREATED
    problemset_id = create_response.json()["id"]

    # Delete it
    delete_response = client.delete(f"/problemsets/{problemset_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's gone by trying to get it
    get_response = client.get(f"/problemsets/{problemset_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


# --- KEEP Existing Tests (Lecture Data, PDF, etc.) ---
# Example of how one might look after adding new ones

# This test might be redundant now with test_read_all_problemsets_...
# Or keep it if it checks something specific about the GET / route
def test_read_all_problemsets_returns_list(client):
     """ Ensure GET /problemsets returns a list, even if empty """
     response = client.get("/problemsets/")
     assert response.status_code == status.HTTP_200_OK
     assert isinstance(response.json(), list)


# Keep tests for the lecture-specific endpoint if still needed
# Example (assuming you have setup data for these)
@pytest.mark.skip(reason="Requires specific DB setup for lecture data tests")
def test_get_lecture_data_success(client, test_db):
     # --- ARRANGE ---
     # Need to manually create a Problemset, Problems, and links in test_db
     # Example:
     # ps = Problemset(id=69, title="Sample Lecture", type="predavanje", ...)
     # p1 = Problem(id=101, latex_text="Problem 1", category="A")
     # p2 = Problem(id=102, latex_text="Problem 2", category="G")
     # link1 = ProblemsetProblems(id_problemset=69, id_problem=101, position=1)
     # link2 = ProblemsetProblems(id_problemset=69, id_problem=102, position=2)
     # test_db.add_all([ps, p1, p2, link1, link2])
     # test_db.commit()
     problemset_id = 69 # Use the ID created

     # --- ACT ---
     response = client.get(f"/problemsets/{problemset_id}/lecture-data")

     # --- ASSERT ---
     assert response.status_code == status.HTTP_200_OK
     data = response.json()
     assert data["id"] == problemset_id
     assert data["title"] == "Sample Lecture" # Check title
     assert len(data["problems"]) == 2 # Check number of problems
     assert data["problems"][0]["position"] == 1
     assert data["problems"][0]["problem"]["latex_text"] == "Problem 1"
     assert data["problems"][1]["position"] == 2
     assert data["problems"][1]["problem"]["latex_text"] == "Problem 2"

@pytest.mark.skip(reason="Requires specific DB setup for lecture data tests")
def test_get_lecture_data_not_found_wrong_id(client):
     response = client.get("/problemsets/999/lecture-data") # Non-existent ID
     assert response.status_code == status.HTTP_404_NOT_FOUND

# You might remove this test if the endpoint now returns any type, not just 'predavanje'
@pytest.mark.skip(reason="Endpoint logic might have changed")
def test_get_lecture_data_not_found_wrong_type(client, test_db):
     # --- ARRANGE ---
     # Create a problemset that is NOT 'predavanje'
     # ps_vjezbe = Problemset(id=70, title="Sample Vjezbe", type="vjezbe", ...)
     # test_db.add(ps_vjezbe)
     # test_db.commit()
     problemset_id = 70

     # --- ACT ---
     # The endpoint might return 200 OK now, or 404 if logic still filters type
     response = client.get(f"/problemsets/{problemset_id}/lecture-data")

     # --- ASSERT ---
     # Adjust assertion based on current endpoint behavior
     # assert response.status_code == status.HTTP_404_NOT_FOUND # If it still filters type
     assert response.status_code == status.HTTP_200_OK # If it returns any type
     if response.status_code == status.HTTP_200_OK:
         assert response.json()["type"] == "vjezbe"


def test_get_lecture_data_invalid_id_format(client):
     response = client.get("/problemsets/invalid-id/lecture-data")
     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Add tests for the PDF download endpoint if desired (more complex)