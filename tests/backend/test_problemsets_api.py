# tests/backend/test_problemsets_api.py

import pytest 
from fastapi import status 
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock

from server.main import app
from server.models.problemset import Problemset, ProblemsetStatusEnum
from server.models.problem import Problem
from server.schemas.problemset import ProblemsetFinalize

client = TestClient(app)

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

# Helper function to create a problem
def create_problem(client, latex_text="Test Problem", category="A"):
    problem_data = {"latex_text": latex_text, "category": category}
    response = client.post("/problems/", json=problem_data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# Helper function to create a problemset
def create_problemset(client, data=None):
    if data is None:
        data = VALID_PROBLEMSET_DATA_1
    response = client.post("/problemsets/", json=data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# Helper function to add a problem to a problemset (using the endpoint)
def link_problem_to_problemset(client, ps_id, p_id, position=None):
    url = f"/problemsets/{ps_id}/problems/{p_id}"
    if position is not None:
        url += f"?position={position}"
    response = client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def assert_problem_order(client, ps_id, expected_p_ids):
    response = client.get(f"/problemsets/{ps_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["problems"]) == len(expected_p_ids)
    # Sort fetched problems by position
    sorted_problems = sorted(data["problems"], key=lambda p: p["position"])
    # Extract IDs in order
    actual_p_ids = [p["problem"]["id"] for p in sorted_problems]
    # Check positions are contiguous and match expected IDs
    for i, p_id in enumerate(expected_p_ids):
        assert sorted_problems[i]["problem"]["id"] == p_id
        assert sorted_problems[i]["position"] == i + 1
    assert actual_p_ids == expected_p_ids


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
    assert isinstance(data["id"], int) # Check ID is present and an integer
    assert "problems" in data # Check problems list exists
    assert isinstance(data["problems"], list) # Check it's a list
    assert len(data["problems"]) == 0 # Should be empty on creation

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
    assert data["type"] == data_no_group["type"]
    assert data["part_of"] == data_no_group["part_of"]
    assert data["group_name"] is None # Verify the optional field is None
    assert "id" in data

def test_read_all_problemsets_empty(client):
    response = client.get("/problemsets/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_read_all_problemsets_with_data(client):
    # Create a couple of problemsets
    ps1 = create_problemset(client, VALID_PROBLEMSET_DATA_1)
    ps2 = create_problemset(client, VALID_PROBLEMSET_DATA_2)

    response = client.get("/problemsets/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    # Check titles and IDs to ensure different items were returned
    ids = {item["id"] for item in data}
    titles = {item["title"] for item in data}
    assert ps1["id"] in ids
    assert ps2["id"] in ids
    assert VALID_PROBLEMSET_DATA_1["title"] in titles
    assert VALID_PROBLEMSET_DATA_2["title"] in titles
    # Check structure of one item
    assert "type" in data[0]
    assert "part_of" in data[0]
    assert "group_name" in data[0]
    assert "problems" in data[0]

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
    assert data["part_of"] == VALID_PROBLEMSET_DATA_1["part_of"]
    assert data["group_name"] == VALID_PROBLEMSET_DATA_1["group_name"]
    assert "problems" in data
    assert isinstance(data["problems"], list)
    assert len(data["problems"]) == 0 # No problems added yet

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
    assert "problems" in updated_data # Should still have problems list

    # Verify by reading again
    get_response = client.get(f"/problemsets/{problemset_id}")
    assert get_response.status_code == status.HTTP_200_OK
    verify_data = get_response.json()
    assert verify_data["title"] == UPDATE_PROBLEMSET_DATA["title"]
    assert verify_data["type"] == UPDATE_PROBLEMSET_DATA["type"]
    assert verify_data["part_of"] == UPDATE_PROBLEMSET_DATA["part_of"]
    assert verify_data["group_name"] == UPDATE_PROBLEMSET_DATA["group_name"]

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

# --- Tests for Adding/Removing Problems (Associations) ---

def test_add_problem_to_problemset_success_append_empty(client):
    # Append to an empty list
    ps = create_problemset(client)
    problem = create_problem(client, "Problem to append")
    ps_id = ps["id"]
    p_id = problem["id"]

    response = client.post(f"/problemsets/{ps_id}/problems/{p_id}") # No position param
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p_id
    assert link_data["position"] == 1
    assert_problem_order(client, ps_id, [p_id])

def test_add_problem_to_problemset_success_append_non_empty(client):
    # Append to a list with one item
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    ps_id = ps["id"]
    p1_id, p2_id = p1["id"], p2["id"]

    link_problem_to_problemset(client, ps_id, p1_id) # Adds p1 at pos 1

    response = client.post(f"/problemsets/{ps_id}/problems/{p2_id}") # Append p2
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p2_id
    assert link_data["position"] == 2 # Should append to pos 2
    assert_problem_order(client, ps_id, [p1_id, p2_id])


def test_add_problem_to_problemset_insert_at_beginning(client):
    # Arrange: ps with p1(pos1)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2 - New First")
    ps_id = ps["id"]
    p1_id, p2_id = p1["id"], p2["id"]
    link_problem_to_problemset(client, ps_id, p1_id) # p1 is at pos 1

    # Act: Insert p2 at position 1
    response = client.post(f"/problemsets/{ps_id}/problems/{p2_id}?position=1")
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p2_id
    assert link_data["position"] == 1

    # Assert: p2 is pos 1, p1 is pos 2
    assert_problem_order(client, ps_id, [p2_id, p1_id])

def test_add_problem_to_problemset_insert_in_middle(client):
    # Arrange: ps with p1(pos1), p3(pos2)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2 - New Middle")
    p3 = create_problem(client, "Problem 3")
    ps_id = ps["id"]
    p1_id, p2_id, p3_id = p1["id"], p2["id"], p3["id"]
    link_problem_to_problemset(client, ps_id, p1_id) # p1 pos 1
    link_problem_to_problemset(client, ps_id, p3_id) # p3 pos 2

    # Act: Insert p2 at position 2
    response = client.post(f"/problemsets/{ps_id}/problems/{p2_id}?position=2")
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p2_id
    assert link_data["position"] == 2

    # Assert: p1 is pos 1, p2 is pos 2, p3 is pos 3
    assert_problem_order(client, ps_id, [p1_id, p2_id, p3_id])

def test_add_problem_to_problemset_insert_at_end_explicit_position(client):
    # Arrange: ps with p1(pos1)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2 - New End")
    ps_id = ps["id"]
    p1_id, p2_id = p1["id"], p2["id"]
    link_problem_to_problemset(client, ps_id, p1_id) # p1 pos 1

    # Act: Insert p2 at position 2 (which is the end)
    response = client.post(f"/problemsets/{ps_id}/problems/{p2_id}?position=2")
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p2_id
    assert link_data["position"] == 2

    # Assert: p1 is pos 1, p2 is pos 2
    assert_problem_order(client, ps_id, [p1_id, p2_id])

def test_add_problem_to_problemset_insert_at_position_greater_than_size(client):
    # Arrange: ps with p1(pos1)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2 - Far Position")
    ps_id = ps["id"]
    p1_id, p2_id = p1["id"], p2["id"]
    link_problem_to_problemset(client, ps_id, p1_id) # p1 pos 1

    # Act: Insert p2 at position 5 (greater than current size + 1)
    # The current service logic should handle this by shifting from pos 5 onwards
    # (which means no shift needed here) and inserting at pos 5.
    # If strict validation is added later to prevent gaps, this test would change.
    response = client.post(f"/problemsets/{ps_id}/problems/{p2_id}?position=5")
    assert response.status_code == status.HTTP_201_CREATED
    link_data = response.json()
    assert link_data["problem"]["id"] == p2_id
    assert link_data["position"] == 5

    # Assert: p1 is pos 1, p2 is pos 5 (assuming no gap filling)
    # We cannot use assert_problem_order directly here due to the gap
    get_response = client.get(f"/problemsets/{ps_id}")
    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert len(data["problems"]) == 2
    problems_map = {p["problem"]["id"]: p["position"] for p in data["problems"]}
    assert problems_map[p1_id] == 1
    assert problems_map[p2_id] == 5


def test_add_problem_to_problemset_insert_at_invalid_position_zero(client):
    ps = create_problemset(client)
    problem = create_problem(client)
    ps_id = ps["id"]
    p_id = problem["id"]

    response = client.post(f"/problemsets/{ps_id}/problems/{p_id}?position=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # FastAPI validation for ge=1

def test_add_problem_to_problemset_insert_at_invalid_position_negative(client):
    ps = create_problemset(client)
    problem = create_problem(client)
    ps_id = ps["id"]
    p_id = problem["id"]

    response = client.post(f"/problemsets/{ps_id}/problems/{p_id}?position=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # FastAPI validation for ge=1

def test_add_problem_to_problemset_non_existent_problemset(client):
    problem = create_problem(client)
    p_id = problem["id"]
    response = client.post(f"/problemsets/9999/problems/{p_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_add_problem_to_problemset_non_existent_problem(client):
    ps = create_problemset(client)
    ps_id = ps["id"]
    response = client.post(f"/problemsets/{ps_id}/problems/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_add_problem_to_problemset_already_linked(client):
    ps = create_problemset(client)
    problem = create_problem(client)
    ps_id = ps["id"]
    p_id = problem["id"]
    client.post(f"/problemsets/{ps_id}/problems/{p_id}") 
    response = client.post(f"/problemsets/{ps_id}/problems/{p_id}") 
    assert response.status_code == status.HTTP_409_CONFLICT

def test_remove_problem_from_problemset_success_middle_element_shifts(client):
    # Arrange: Create ps, p1, p2, p3. Link p1(pos1), p2(pos2), p3(pos3)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    p3 = create_problem(client, "Problem 3")
    ps_id = ps["id"]
    p1_id, p2_id, p3_id = p1["id"], p2["id"], p3["id"]

    link_problem_to_problemset(client, ps_id, p1_id) # pos 1
    link_problem_to_problemset(client, ps_id, p2_id) # pos 2
    link_problem_to_problemset(client, ps_id, p3_id) # pos 3

    # Act: Delete the middle problem (p2 at pos 2)
    response = client.delete(f"/problemsets/{ps_id}/problems/{p2_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Assert: Verify p1 is pos 1, p3 is now pos 2
    ps_response = client.get(f"/problemsets/{ps_id}")
    assert ps_response.status_code == status.HTTP_200_OK
    ps_data = ps_response.json()
    assert len(ps_data["problems"]) == 2

    # Sort results by position for reliable assertion
    sorted_problems = sorted(ps_data["problems"], key=lambda x: x["position"])

    assert sorted_problems[0]["problem"]["id"] == p1_id
    assert sorted_problems[0]["position"] == 1
    assert sorted_problems[1]["problem"]["id"] == p3_id
    assert sorted_problems[1]["position"] == 2 # Position shifted from 3 to 2

def test_remove_problem_from_problemset_success_first_element_shifts(client):
    # Arrange: Create ps, p1, p2, p3. Link p1(pos1), p2(pos2), p3(pos3)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    p3 = create_problem(client, "Problem 3")
    ps_id = ps["id"]
    p1_id, p2_id, p3_id = p1["id"], p2["id"], p3["id"]

    link_problem_to_problemset(client, ps_id, p1_id) # pos 1
    link_problem_to_problemset(client, ps_id, p2_id) # pos 2
    link_problem_to_problemset(client, ps_id, p3_id) # pos 3

    # Act: Delete the first problem (p1 at pos 1)
    response = client.delete(f"/problemsets/{ps_id}/problems/{p1_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Assert: Verify p2 is pos 1, p3 is pos 2
    ps_response = client.get(f"/problemsets/{ps_id}")
    assert ps_response.status_code == status.HTTP_200_OK
    ps_data = ps_response.json()
    assert len(ps_data["problems"]) == 2

    sorted_problems = sorted(ps_data["problems"], key=lambda x: x["position"])

    assert sorted_problems[0]["problem"]["id"] == p2_id
    assert sorted_problems[0]["position"] == 1 # Position shifted from 2 to 1
    assert sorted_problems[1]["problem"]["id"] == p3_id
    assert sorted_problems[1]["position"] == 2 # Position shifted from 3 to 2

def test_remove_problem_from_problemset_success_last_element_no_shift(client):
    # Arrange: Create ps, p1, p2. Link p1(pos1), p2(pos2)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    ps_id = ps["id"]
    p1_id, p2_id = p1["id"], p2["id"]

    link_problem_to_problemset(client, ps_id, p1_id) # pos 1
    link_problem_to_problemset(client, ps_id, p2_id) # pos 2

    # Act: Delete the last problem (p2 at pos 2)
    response = client.delete(f"/problemsets/{ps_id}/problems/{p2_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Assert: Verify p1 is still pos 1
    ps_response = client.get(f"/problemsets/{ps_id}")
    assert ps_response.status_code == status.HTTP_200_OK
    ps_data = ps_response.json()
    assert len(ps_data["problems"]) == 1

    assert ps_data["problems"][0]["problem"]["id"] == p1_id
    assert ps_data["problems"][0]["position"] == 1 # Position remains unchanged

def test_remove_problem_from_problemset_success_only_element(client):
    # Arrange: Create ps, p1. Link p1(pos1)
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    ps_id = ps["id"]
    p1_id = p1["id"]

    link_problem_to_problemset(client, ps_id, p1_id) # pos 1

    # Act: Delete the only problem
    response = client.delete(f"/problemsets/{ps_id}/problems/{p1_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Assert: Verify problemset is empty
    ps_response = client.get(f"/problemsets/{ps_id}")
    assert ps_response.status_code == status.HTTP_200_OK
    ps_data = ps_response.json()
    assert len(ps_data["problems"]) == 0


def test_remove_problem_from_problemset_not_linked(client):
    ps = create_problemset(client)
    problem = create_problem(client)
    ps_id = ps["id"]
    p_id = problem["id"]
    response = client.delete(f"/problemsets/{ps_id}/problems/{p_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Problem association not found" in response.json()["detail"]

def test_remove_problem_from_problemset_non_existent_problemset(client):
    problem = create_problem(client)
    p_id = problem["id"]
    response = client.delete(f"/problemsets/9999/problems/{p_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Problem association not found" in response.json()["detail"]

def test_remove_problem_from_problemset_non_existent_problem(client):
    ps = create_problemset(client)
    ps_id = ps["id"]
    response = client.delete(f"/problemsets/{ps_id}/problems/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Problem association not found" in response.json()["detail"]

# --- NEW TESTS FOR REORDERING PROBLEMS ---

def test_reorder_problems_success(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    p3 = create_problem(client, "Problem 3")
    ps_id = ps["id"]
    
    # Link in order 1, 2, 3 initially
    link_problem_to_problemset(client, ps_id, p1["id"])
    link_problem_to_problemset(client, ps_id, p2["id"])
    link_problem_to_problemset(client, ps_id, p3["id"])
    
    new_order = [p3["id"], p1["id"], p2["id"]]
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data["problems"]) == 3
    assert data["problems"][0]["problem"]["id"] == p3["id"]
    assert data["problems"][0]["position"] == 1
    assert data["problems"][1]["problem"]["id"] == p1["id"]
    assert data["problems"][1]["position"] == 2
    assert data["problems"][2]["problem"]["id"] == p2["id"]
    assert data["problems"][2]["position"] == 3
    
    # Verify by getting again
    get_response = client.get(f"/problemsets/{ps_id}")
    verify_data = get_response.json()
    assert len(verify_data["problems"]) == 3
    assert verify_data["problems"][0]["problem"]["id"] == p3["id"]
    assert verify_data["problems"][0]["position"] == 1
    assert verify_data["problems"][1]["problem"]["id"] == p1["id"]
    assert verify_data["problems"][1]["position"] == 2
    assert verify_data["problems"][2]["problem"]["id"] == p2["id"]
    assert verify_data["problems"][2]["position"] == 3

def test_reorder_problems_no_change(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    ps_id = ps["id"]
    
    link_problem_to_problemset(client, ps_id, p1["id"]) # pos 1
    link_problem_to_problemset(client, ps_id, p2["id"]) # pos 2
    
    new_order = [p1["id"], p2["id"]]
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data["problems"]) == 2
    assert data["problems"][0]["problem"]["id"] == p1["id"]
    assert data["problems"][0]["position"] == 1
    assert data["problems"][1]["problem"]["id"] == p2["id"]
    assert data["problems"][1]["position"] == 2

def test_reorder_problems_single_problem(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    ps_id = ps["id"]
    
    link_problem_to_problemset(client, ps_id, p1["id"]) # pos 1
    
    new_order = [p1["id"]]
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    assert len(data["problems"]) == 1
    assert data["problems"][0]["problem"]["id"] == p1["id"]
    assert data["problems"][0]["position"] == 1

def test_reorder_problems_empty_problemset(client):
    ps = create_problemset(client)
    ps_id = ps["id"]
    
    new_order = []
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["problems"]) == 0

def test_reorder_problems_problemset_not_found(client):
    payload = {"problem_ids_ordered": [1, 2]}
    response = client.put("/problemsets/9999/problems/order", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_reorder_problems_mismatched_count_omitted(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    ps_id = ps["id"]
    
    link_problem_to_problemset(client, ps_id, p1["id"])
    link_problem_to_problemset(client, ps_id, p2["id"])
    
    new_order = [p1["id"]] # Omitting p2
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "omitted from the new order" in response.json()["detail"]

def test_reorder_problems_mismatched_count_added(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p_extra = create_problem(client, "Extra Problem") # Not linked
    ps_id = ps["id"]
    
    link_problem_to_problemset(client, ps_id, p1["id"])
    
    new_order = [p1["id"], p_extra["id"]] # Trying to add p_extra
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # The error might be about the problem not being in the set OR about the count mismatch
    assert "not found in problemset" in response.json()["detail"] or "Mismatch in the number of problems" in response.json()["detail"]


def test_reorder_problems_id_not_in_set(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p_not_linked = create_problem(client, "Not Linked")
    ps_id = ps["id"]
    
    link_problem_to_problemset(client, ps_id, p1["id"])
    
    new_order = [p_not_linked["id"]] # p_not_linked is not in the set
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"Problem IDs {{{p_not_linked['id']}}} not found in problemset" in response.json()["detail"]

def test_reorder_problems_duplicate_ids_in_order(client):
    ps = create_problemset(client)
    p1 = create_problem(client, "Problem 1")
    p2 = create_problem(client, "Problem 2")
    ps_id = ps["id"]
    
    link_problem_to_problemset(client, ps_id, p1["id"])
    link_problem_to_problemset(client, ps_id, p2["id"])
    
    new_order = [p1["id"], p1["id"]] # Duplicate p1
    payload = {"problem_ids_ordered": new_order}
    
    response = client.put(f"/problemsets/{ps_id}/problems/order", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Duplicate problem IDs provided" in response.json()["detail"]

# --- KEEP Existing Tests (Lecture Data, PDF, etc.) ---
# ... (rest of the existing tests remain) ...
@pytest.mark.skip(reason="Requires specific DB setup for lecture data tests")
def test_get_lecture_data_success(client, test_db):
     problemset_id = 69 
     response = client.get(f"/problemsets/{problemset_id}/lecture-data")
     # ... assertions ...

@pytest.mark.skip(reason="Requires specific DB setup for lecture data tests")
def test_get_lecture_data_not_found_wrong_id(client):
     response = client.get("/problemsets/999/lecture-data") 
     assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.skip(reason="Endpoint logic might have changed")
def test_get_lecture_data_not_found_wrong_type(client, test_db):
     problemset_id = 70
     response = client.get(f"/problemsets/{problemset_id}/lecture-data")
     # ... assertions ...

def test_get_lecture_data_invalid_id_format(client):
     response = client.get("/problemsets/invalid-id/lecture-data")
     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY