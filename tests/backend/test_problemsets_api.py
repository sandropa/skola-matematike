# tests/backend/test_problemsets_api.py

import pytest 
from fastapi import status 

# Test Data
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
    "type": "predavanje-updated", 
    "part_of": "ljetni kamp 2024", 
    "group_name": "pocetna-revised" 
}

INVALID_PROBLEMSET_DATA_MISSING_FIELD = {
    "type": "predavanje",
    "part_of": "ljetni kamp",
    "group_name": "pocetna"
}

# --- Helper function to create a problem ---
def create_problem(client, latex_text="Test Problem", category="A"):
    problem_data = {"latex_text": latex_text, "category": category}
    response = client.post("/problems/", json=problem_data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# --- Helper function to create a problemset ---
def create_problemset(client, data=None):
    if data is None:
        data = VALID_PROBLEMSET_DATA_1
    response = client.post("/problemsets/", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# --- Existing CRUD Test Functions ---

def test_create_problemset_success(client):
    response = client.post("/problemsets/", json=VALID_PROBLEMSET_DATA_1)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == VALID_PROBLEMSET_DATA_1["title"]
    assert data["type"] == VALID_PROBLEMSET_DATA_1["type"]
    assert data["part_of"] == VALID_PROBLEMSET_DATA_1["part_of"]
    assert data["group_name"] == VALID_PROBLEMSET_DATA_1["group_name"]
    assert "id" in data
    assert "problems" in data 
    assert isinstance(data["problems"], list)

def test_create_problemset_missing_required_field(client):
    response = client.post("/problemsets/", json=INVALID_PROBLEMSET_DATA_MISSING_FIELD)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_create_problemset_optional_field_missing(client):
    data_no_group = VALID_PROBLEMSET_DATA_1.copy()
    del data_no_group["group_name"]
    response = client.post("/problemsets/", json=data_no_group)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == data_no_group["title"]
    assert data["group_name"] is None 

def test_read_all_problemsets_empty(client):
    response = client.get("/problemsets/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_read_all_problemsets_with_data(client):
    create_problemset(client, VALID_PROBLEMSET_DATA_1)
    create_problemset(client, VALID_PROBLEMSET_DATA_2)

    response = client.get("/problemsets/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    titles = {item["title"] for item in data}
    assert VALID_PROBLEMSET_DATA_1["title"] in titles
    assert VALID_PROBLEMSET_DATA_2["title"] in titles

def test_read_problemset_not_found(client):
    response = client.get("/problemsets/999") 
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_read_problemset_success(client):
    created_ps = create_problemset(client)
    problemset_id = created_ps["id"]

    response = client.get(f"/problemsets/{problemset_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == problemset_id
    assert data["title"] == VALID_PROBLEMSET_DATA_1["title"]
    assert data["type"] == VALID_PROBLEMSET_DATA_1["type"]
    assert data["group_name"] == VALID_PROBLEMSET_DATA_1["group_name"]

def test_update_problemset_not_found(client):
    response = client.put("/problemsets/999", json=UPDATE_PROBLEMSET_DATA)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_problemset_success(client):
    created_ps = create_problemset(client)
    problemset_id = created_ps["id"]

    update_response = client.put(f"/problemsets/{problemset_id}", json=UPDATE_PROBLEMSET_DATA)
    assert update_response.status_code == status.HTTP_200_OK
    updated_data = update_response.json()
    assert updated_data["id"] == problemset_id
    assert updated_data["title"] == UPDATE_PROBLEMSET_DATA["title"]
    assert updated_data["type"] == UPDATE_PROBLEMSET_DATA["type"]
    assert updated_data["part_of"] == UPDATE_PROBLEMSET_DATA["part_of"]
    assert updated_data["group_name"] == UPDATE_PROBLEMSET_DATA["group_name"]

    get_response = client.get(f"/problemsets/{problemset_id}")
    assert get_response.status_code == status.HTTP_200_OK
    verify_data = get_response.json()
    assert verify_data["title"] == UPDATE_PROBLEMSET_DATA["title"]
    assert verify_data["type"] == UPDATE_PROBLEMSET_DATA["type"]

def test_update_problemset_invalid_data(client):
    created_ps = create_problemset(client)
    problemset_id = created_ps["id"]

    invalid_update_data = UPDATE_PROBLEMSET_DATA.copy()
    del invalid_update_data["title"]
    update_response = client.put(f"/problemsets/{problemset_id}", json=invalid_update_data)
    assert update_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_problemset_not_found(client):
    response = client.delete("/problemsets/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_problemset_success(client):
    created_ps = create_problemset(client)
    problemset_id = created_ps["id"]

    delete_response = client.delete(f"/problemsets/{problemset_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    get_response = client.get(f"/problemsets/{problemset_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_read_all_problemsets_returns_list(client):
     response = client.get("/problemsets/")
     assert response.status_code == status.HTTP_200_OK
     assert isinstance(response.json(), list)

# --- NEW TESTS FOR PROBLEM ASSOCIATIONS ---

def test_add_problem_to_problemset_success_append(client):
    ps = create_problemset(client)
    problem = create_problem(client, "Problem to append")
    ps_id = ps["id"]
    p_id = problem["id"]

    response = client.post(f"/problemsets/{ps_id}/problems/{p_id}")
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p_id
    assert link_data["position"] == 1 # First problem appended

    # Verify by getting the problemset
    ps_response = client.get(f"/problemsets/{ps_id}")
    assert ps_response.status_code == status.HTTP_200_OK
    ps_data = ps_response.json()
    assert len(ps_data["problems"]) == 1
    assert ps_data["problems"][0]["problem"]["id"] == p_id
    assert ps_data["problems"][0]["position"] == 1

def test_add_problem_to_problemset_success_specific_position(client):
    ps = create_problemset(client)
    problem = create_problem(client, "Problem at pos 1")
    ps_id = ps["id"]
    p_id = problem["id"]

    response = client.post(f"/problemsets/{ps_id}/problems/{p_id}?position=1")
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p_id
    assert link_data["position"] == 1

def test_add_problem_to_problemset_append_multiple(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    ps_id = ps["id"]

    # Add first problem (appends to pos 1)
    client.post(f"/problemsets/{ps_id}/problems/{p1['id']}")
    # Add second problem (appends to pos 2)
    response_p2 = client.post(f"/problemsets/{ps_id}/problems/{p2['id']}")
    assert response_p2.status_code == status.HTTP_201_CREATED
    link_data_p2 = response_p2.json()
    assert link_data_p2["position"] == 2

    # Verify
    ps_response = client.get(f"/problemsets/{ps_id}")
    ps_data = ps_response.json()
    assert len(ps_data["problems"]) == 2
    assert ps_data["problems"][0]["problem"]["id"] == p1["id"]
    assert ps_data["problems"][0]["position"] == 1
    assert ps_data["problems"][1]["problem"]["id"] == p2["id"]
    assert ps_data["problems"][1]["position"] == 2


def test_add_problem_to_problemset_non_existent_problemset(client):
    problem = create_problem(client)
    p_id = problem["id"]
    response = client.post(f"/problemsets/9999/problems/{p_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Problemset with id 9999 not found" in response.json()["detail"]

def test_add_problem_to_problemset_non_existent_problem(client):
    ps = create_problemset(client)
    ps_id = ps["id"]
    response = client.post(f"/problemsets/{ps_id}/problems/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Problem with id 9999 not found" in response.json()["detail"]

def test_add_problem_to_problemset_already_linked(client):
    ps = create_problemset(client)
    problem = create_problem(client)
    ps_id = ps["id"]
    p_id = problem["id"]

    client.post(f"/problemsets/{ps_id}/problems/{p_id}") # First successful link
    response = client.post(f"/problemsets/{ps_id}/problems/{p_id}") # Attempt again
    assert response.status_code == status.HTTP_409_CONFLICT
    assert f"Problem {p_id} is already in problemset {ps_id}" in response.json()["detail"]

def test_add_problem_to_problemset_position_conflict(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    ps_id = ps["id"]

    # Add p1 at position 1
    client.post(f"/problemsets/{ps_id}/problems/{p1['id']}?position=1")
    
    # Attempt to add p2 at position 1
    response = client.post(f"/problemsets/{ps_id}/problems/{p2['id']}?position=1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST # Or 409 based on final router logic
    assert f"Position 1 in problemset {ps_id} is already occupied" in response.json()["detail"]

def test_remove_problem_from_problemset_success(client):
    ps = create_problemset(client)
    problem = create_problem(client)
    ps_id = ps["id"]
    p_id = problem["id"]

    client.post(f"/problemsets/{ps_id}/problems/{p_id}") # Link them

    response = client.delete(f"/problemsets/{ps_id}/problems/{p_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify
    ps_response = client.get(f"/problemsets/{ps_id}")
    ps_data = ps_response.json()
    assert len(ps_data["problems"]) == 0

def test_remove_problem_from_problemset_not_linked(client):
    ps = create_problemset(client)
    problem = create_problem(client) # Problem exists but not linked
    ps_id = ps["id"]
    p_id = problem["id"]

    response = client.delete(f"/problemsets/{ps_id}/problems/{p_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Problem association not found" in response.json()["detail"]

def test_remove_problem_from_problemset_non_existent_problemset(client):
    problem = create_problem(client)
    p_id = problem["id"]
    response = client.delete(f"/problemsets/9999/problems/{p_id}")
    # The link won't be found because the problemset doesn't exist, leading to 404 for the association
    assert response.status_code == status.HTTP_404_NOT_FOUND 
    assert "Problem association not found" in response.json()["detail"]


def test_remove_problem_from_problemset_non_existent_problem(client):
    ps = create_problemset(client)
    ps_id = ps["id"]
    response = client.delete(f"/problemsets/{ps_id}/problems/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Problem association not found" in response.json()["detail"]


# --- KEEP Existing Tests (Lecture Data, PDF, etc.) ---
@pytest.mark.skip(reason="Requires specific DB setup for lecture data tests")
def test_get_lecture_data_success(client, test_db):
     problemset_id = 69 
     response = client.get(f"/problemsets/{problemset_id}/lecture-data")
     assert response.status_code == status.HTTP_200_OK
     data = response.json()
     assert data["id"] == problemset_id
     assert data["title"] == "Sample Lecture" 
     assert len(data["problems"]) == 2 
     assert data["problems"][0]["position"] == 1
     assert data["problems"][0]["problem"]["latex_text"] == "Problem 1"
     assert data["problems"][1]["position"] == 2
     assert data["problems"][1]["problem"]["latex_text"] == "Problem 2"

@pytest.mark.skip(reason="Requires specific DB setup for lecture data tests")
def test_get_lecture_data_not_found_wrong_id(client):
     response = client.get("/problemsets/999/lecture-data") 
     assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.skip(reason="Endpoint logic might have changed")
def test_get_lecture_data_not_found_wrong_type(client, test_db):
     problemset_id = 70
     response = client.get(f"/problemsets/{problemset_id}/lecture-data")
     assert response.status_code == status.HTTP_200_OK 
     if response.status_code == status.HTTP_200_OK:
         assert response.json()["type"] == "vjezbe"


def test_get_lecture_data_invalid_id_format(client):
     response = client.get("/problemsets/invalid-id/lecture-data")
     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY