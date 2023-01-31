import tempfile

from chanjo2.constants import SUCCESS_CODE, UNPROCESSABLE_ENTITY

CASES_ENDPOINT = "/cases/"
SAMPLES_ENDPOINT = "/samples/"


def test_create_case(client, test_case):
    """Test the endpoint used to create a new case"""
    # GIVEN a json-like object containing the new case data:
    case_data = test_case

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


def test_create_sample_for_case_no_coverage_file(client):
    """Test the function that creates a new sample for a case when no coverage file is specified"""
    # GIVEN a json-like object containing the new sample data that is missing the coverage_file_path key/Value:
    COVERAGE_FILE_PATH = "FOO"
    sample_data = {
        "name": "abc",
        "display_name": "sample_abc",
        "case_name": "case_123",
        "coverage_file_path": COVERAGE_FILE_PATH,
    }

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(SAMPLES_ENDPOINT, json=sample_data)

    # THEN the response should return error
    assert response.status_code == UNPROCESSABLE_ENTITY
    result = response.json()

    # WITH a meaningful message
    assert response.json()["detail"] == f"Could not find file: {COVERAGE_FILE_PATH}"


def test_create_sample_for_case_no_case(client, test_case):
    """Test the function that creates a new sample for a case when no case was previously saved in the database"""

    # GIVEN a json-like object containing the new sample data:
    with tempfile.NamedTemporaryFile(suffix=".d4") as tf:
        sample_data = {
            "name": "abc",
            "display_name": "sample_abc",
            "case_name": test_case["name"],
            "coverage_file_path": tf.name,
        }

        # WHEN the create_sample_for_case endpoint is used to create the case
        response = client.post(SAMPLES_ENDPOINT, json=sample_data)

        # THEN the response should return error
        assert response.status_code == UNPROCESSABLE_ENTITY
        result = response.json()

        # WITH a meaningful message
        assert response.json()["detail"] == "Could not find a case for this sample"


def test_create_sample_for_case(test_case, client):
    """Test the function that creates a new sample for a case when provided sample info is complete"""

    # GIVEN a case that exists in the database:
    saved_case = client.post(CASES_ENDPOINT, json=test_case).json()

    # GIVEN a json-like object containing the new sample data:
    with tempfile.NamedTemporaryFile(suffix=".d4") as tf:
        sample_data = {
            "name": "abc",
            "display_name": "sample_abc",
            "case_name": test_case["name"],
            "coverage_file_path": tf.name,
        }

        # WHEN the create_sample_for_case endpoint is used to create the case
        response = client.post(SAMPLES_ENDPOINT, json=sample_data)

        # THEN the response shour return success
        assert response.status_code == SUCCESS_CODE

        # AND the saved data should be correct
        saved_sample = response.json()
        assert saved_sample["id"]
        assert saved_sample["created_at"]
        for item in ["name", "display_name", "coverage_file_path"]:
            assert saved_sample[item] == sample_data[item]
        assert saved_sample["case_id"] == saved_case["id"]
