import pytest
from chanjo2.constants import SUCCESS_CODE

CASES_ENDPOINT = "/cases/"


def pytest_namespace():
    return {"shared": None}


def test_create_case(client):
    """Test the endpoint used to create a new case"""
    # GIVEN a json-like object containing the new case data:
    case_data = {"name": "case_id", "display_name": "case_name"}

    # WHEN the create_case endpoint is used to create the case
    response = client.post(CASES_ENDPOINT, json=case_data)

    # THEN it should return success
    assert response.status_code == SUCCESS_CODE

    # AND the case should have been saved correctly
    saved_case = response.json()
    for key, _ in case_data.items():
        assert saved_case[key] == case_data[key]

    # WHEN sending a GET request to fetch all database cases
    response = client.get(CASES_ENDPOINT)

    # THEN it should return success
    assert response.status_code == SUCCESS_CODE

    # AND the case should be returned in the list of results:
    for item in response.json():
        for key, _ in case_data.items():
            assert item[key] == case_data[key]

    # WHEN sending a GET request to retrieve the specific case using its name:
    response = client.get(f"{CASES_ENDPOINT}{case_data['name']}")

    # THEN it should also return success
    assert response.status_code == SUCCESS_CODE
    result = response.json()

    # AND the case object should be returned as result
    for key, _ in case_data.items():
        assert result[key] == case_data[key]
