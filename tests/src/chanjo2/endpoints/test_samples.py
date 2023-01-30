CASES_ENDPOINT = "/cases/"
from chanjo2.constants import SUCCESS_CODE


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
