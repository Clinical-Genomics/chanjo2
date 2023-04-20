from pathlib import PosixPath
from typing import Dict, Type

from chanjo2.models.pydantic_models import WRONG_COVERAGE_FILE_MSG, Sample
from chanjo2.populate_demo import DEMO_CASE, DEMO_SAMPLE
from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture


def test_create_sample_for_case_no_local_coverage_file(
    client: TestClient,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    endpoints: Type,
    mock_coverage_file: str,
):
    """Test the function that creates a new sample for a case when no coverage file is specified."""
    # GIVEN a json-like object containing the new sample data that is missing the coverage_file_path key/Value:
    raw_sample["coverage_file_path"] = mock_coverage_file

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(endpoints.SAMPLES, json=raw_sample)

    # THEN the response should return error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    result = response.json()

    # WITH a meaningful message
    assert result["detail"][0]["msg"] == WRONG_COVERAGE_FILE_MSG


def test_create_sample_for_case_no_remote_coverage_file(
    client: TestClient,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    endpoints: Type,
    remote_coverage_file: str,
):
    """Test the function that creates a new sample for a case with remote coverage file not existing."""
    # GIVEN a json-like object containing the new sample data that is missing the coverage_file_path key/Value:
    raw_sample["coverage_file_path"] = remote_coverage_file

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(endpoints.SAMPLES, json=raw_sample)

    # THEN the response should return error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # WITH a meaningful message
    result = response.json()
    assert result["detail"][0]["msg"] == WRONG_COVERAGE_FILE_MSG


def test_create_sample_for_case_no_case(
    client: TestClient,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    coverage_path: PosixPath,
    endpoints: Type,
):
    """Test the function that creates a new sample for a case when no case was previously saved in the database."""

    # GIVEN a json-like object containing the new sample data:
    raw_sample["coverage_file_path"] = str(coverage_path)

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(endpoints.SAMPLES, json=raw_sample)

    # THEN the response should return error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    result = response.json()

    # WITH a meaningful message
    assert result["detail"] == f"Could not find a case with name: {raw_case['name']}"


def test_create_sample_for_case_local_coverage_file(
    client: TestClient,
    coverage_path: PosixPath,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    endpoints: Type,
):
    """Test the function that creates a new sample for a case with a local coverage file."""

    # GIVEN a case that exists in the database:
    client.post(endpoints.CASES, json=raw_case).json()

    # GIVEN a json-like object containing the new sample data:
    raw_sample["coverage_file_path"] = str(coverage_path)

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(endpoints.SAMPLES, json=raw_sample)

    # THEN the response shour return success
    assert response.status_code == status.HTTP_200_OK

    # AND the saved data should be a Sample object
    result = response.json()
    assert Sample(**result)


def test_create_sample_for_case_remote_coverage_file(
    client: TestClient,
    remote_coverage_file: str,
    coverage_path: PosixPath,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    endpoints: Type,
    mocker: MockerFixture,
):
    """Test the function that creates a new sample for a case with a remote coverage file."""

    # GIVEN a mocked d4 file hosted on the internet
    mocker.patch("validators.url", return_value=True)

    # GIVEN a case that exists in the database:
    client.post(endpoints.CASES, json=raw_case).json()

    # GIVEN a json-like object containing the new sample data:
    raw_sample["coverage_file_path"] = remote_coverage_file

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(endpoints.SAMPLES, json=raw_sample)

    # THEN the response shour return success
    assert response.status_code == status.HTTP_200_OK

    # AND the saved data should be a Sample object
    result = response.json()
    assert Sample(**result)


def test_read_samples(
    demo_client: TestClient,
    endpoints: Type,
):
    """Test endpoint that returns all samples present in the database."""

    # GIVEN a populated demo database
    # THEN the read_samples endpoint should return the sample in the right format
    response = demo_client.get(endpoints.SAMPLES)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == 1
    assert Sample(**result[0])


def test_read_samples_for_case(
    demo_client: TestClient,
    endpoints: Type,
):
    """Test the endpoint that returns all samples for a given case name."""

    # GIVEN a populated demo database
    # THEN the read_samples_for_case endpoint should return the sample
    url = f"/{DEMO_CASE['name']}{endpoints.SAMPLES}"
    response = demo_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert Sample(**result[0])


def test_read_sample(
    demo_client: TestClient,
    endpoints: Type,
):
    """Test the endpoint that returns a single sample when providing its name."""

    # GIVEN a populated demo database
    # THEN the read_sample endpoint should return the sample
    url = f"{endpoints.SAMPLES}{DEMO_SAMPLE['name']}"
    response = demo_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert Sample(**result)
