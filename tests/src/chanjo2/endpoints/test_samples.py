import tempfile

from fastapi import status

SAMPLES_ENDPOINT = "/samples/"
CASES_ENDPOINT = "/cases/"


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
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    result = response.json()

    # WITH a meaningful message
    assert response.json()["detail"] == f"Could not find file: {COVERAGE_FILE_PATH}"


def test_create_sample_for_case_no_case(client, test_case, test_sample):
    """Test the function that creates a new sample for a case when no case was previously saved in the database"""

    # GIVEN a json-like object containing the new sample data:
    with tempfile.NamedTemporaryFile(suffix=".d4") as tf:
        sample_data = {
            "name": test_sample["name"],
            "display_name": test_sample["display_name"],
            "case_name": test_case["name"],
            "coverage_file_path": tf.name,
        }

        # WHEN the create_sample_for_case endpoint is used to create the case
        response = client.post(SAMPLES_ENDPOINT, json=sample_data)

        # THEN the response should return error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
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
        assert response.status_code == status.HTTP_200_OK

        # AND the saved data should be correct
        saved_sample = response.json()
        assert saved_sample["id"]
        assert saved_sample["created_at"]
        for item in ["name", "display_name", "coverage_file_path"]:
            assert saved_sample[item] == sample_data[item]
        assert saved_sample["case_id"] == saved_case["id"]


def test_read_samples(client, session, db_case, db_sample):
    """Test endpoint that returns all samples present in the database"""

    # GIVEN a case object saved in the database
    session.add(db_case)
    session.commit()
    session.refresh(db_case)

    # Which contains a sample
    session.add(db_sample)
    session.commit()
    session.refresh(db_sample)

    # THEN the read_samples endpoint should return the sample:
    response = client.get(SAMPLES_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == 1
    assert result[0]["name"] == db_sample.name


def test_read_samples_for_case(session, client, db_case, db_sample):
    """Test the endpoint that returns all samples for a given case name"""

    # GIVEN a case object saved in the database
    session.add(db_case)
    session.commit()
    session.refresh(db_case)

    # Which contains a sample
    session.add(db_sample)
    session.commit()
    session.refresh(db_sample)

    # THEN the read_samples_for_case endpoint should return the sample
    url = f"/{db_case.name}{SAMPLES_ENDPOINT}"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result[0]["name"] == db_sample.name


def test_read_sample(session, client, db_case, db_sample):
    """Test the ednpoint that returns a single sample when providing its name"""

    # GIVEN a case object saved in the database
    session.add(db_case)
    session.commit()
    session.refresh(db_case)

    # Which contains a sample
    session.add(db_sample)
    session.commit()
    session.refresh(db_sample)

    # THEN the read_sample endpoint should return the sample
    url = f"{SAMPLES_ENDPOINT}{db_sample.name}"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["name"] == db_sample.name
