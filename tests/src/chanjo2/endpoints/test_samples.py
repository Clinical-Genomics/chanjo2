from pathlib import PosixPath
from typing import Dict, Type

import responses
from chanjo2.models.pydantic_models import Sample
from chanjo2.models.sql_models import Case as SQLCase
from chanjo2.models.sql_models import Sample as SQLSample
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


def test_create_sample_for_case_no_local_coverage_file(
    client: TestClient,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    samples_endpoint: str,
    coverage_file: str,
):
    """Test the function that creates a new sample for a case when no coverage file is specified."""
    # GIVEN a json-like object containing the new sample data that is missing the coverage_file_path key/Value:
    sample_data = {
        "name": raw_sample["name"],
        "display_name": raw_sample["display_name"],
        "case_name": raw_case["name"],
        "coverage_file_path": coverage_file,
    }

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(samples_endpoint, json=sample_data)

    # THEN the response should return error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    result = response.json()

    # WITH a meaningful message
    assert result["detail"] == f"Could not find local resource: {coverage_file}"


def test_create_sample_for_case_no_remote_coverage_file(
    client: TestClient,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    samples_endpoint: str,
    remote_coverage_file: str,
):
    """Test the function that creates a new sample for a case when no coverage file is specified."""
    # GIVEN a json-like object containing the new sample data that is missing the coverage_file_path key/Value:
    sample_data = {
        "name": raw_sample["name"],
        "display_name": raw_sample["display_name"],
        "case_name": raw_case["name"],
        "coverage_file_path": remote_coverage_file,
    }

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(samples_endpoint, json=sample_data)

    # THEN the response should return error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    result = response.json()

    # WITH a meaningful message
    assert result["detail"] == f"Could not find remote resource: {remote_coverage_file}"


def test_create_sample_for_case_no_case(
    client: TestClient,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    coverage_path: PosixPath,
    samples_endpoint: str,
):
    """Test the function that creates a new sample for a case when no case was previously saved in the database."""

    # GIVEN a json-like object containing the new sample data:
    sample_data = {
        "name": raw_sample["name"],
        "display_name": raw_sample["display_name"],
        "case_name": raw_case["name"],
        "coverage_file_path": str(coverage_path),
    }

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(samples_endpoint, json=sample_data)

    # THEN the response should return error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    result = response.json()

    # WITH a meaningful message
    assert result["detail"] == f"Could not find a case with name: {raw_case['name']}"


@responses.activate
def test_create_sample_for_case_local_coverage_file(
    client: TestClient,
    coverage_path: PosixPath,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    cases_endpoint: str,
    samples_endpoint: str,
):
    """Test the function that creates a new sample for a case with a local coverage file."""

    # GIVEN a case that exists in the database:
    saved_case = client.post(cases_endpoint, json=raw_case).json()

    # GIVEN a json-like object containing the new sample data:
    sample_data = {
        "name": raw_sample["name"],
        "display_name": raw_sample["display_name"],
        "case_name": raw_case["name"],
        "coverage_file_path": str(coverage_path),
    }

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(samples_endpoint, json=sample_data)

    # THEN the response shour return success
    assert response.status_code == status.HTTP_200_OK

    # AND the saved data should be a Sample object
    result = response.json()
    assert Sample(**result)


@responses.activate
def test_create_sample_for_case_remote_coverage_file(
    client: TestClient,
    remote_coverage_file: str,
    coverage_path: PosixPath,
    raw_case: Dict[str, str],
    raw_sample: Dict[str, str],
    cases_endpoint: str,
    samples_endpoint: str,
):
    """Test the function that creates a new sample for a case with a remote coverage file."""

    assert coverage_path.read_text() == "content"

    # GIVEN a mocked d4 file hosted on the internet
    responses.add(
        responses.HEAD,
        remote_coverage_file,
        body=coverage_path.read_text(),
        status=200,
        content_type="application/octet-stream",
    )

    # GIVEN a case that exists in the database:
    saved_case = client.post(cases_endpoint, json=raw_case).json()

    # GIVEN a json-like object containing the new sample data:
    sample_data = {
        "name": raw_sample["name"],
        "display_name": raw_sample["display_name"],
        "case_name": raw_case["name"],
        "coverage_file_path": remote_coverage_file,
    }

    # WHEN the create_sample_for_case endpoint is used to create the case
    response = client.post(samples_endpoint, json=sample_data)

    # THEN the response shour return success
    assert response.status_code == status.HTTP_200_OK

    # AND the saved data should be a Sample object
    result = response.json()
    assert Sample(**result)


def test_read_samples(
    client: TestClient,
    session: sessionmaker,
    db_case: SQLCase,
    db_sample: SQLSample,
    samples_endpoint: str,
    helpers: Type,
):
    """Test endpoint that returns all samples present in the database."""

    # GIVEN a case object saved in the database
    helpers.session_commit_item(session, db_case)

    # Which contains a sample
    helpers.session_commit_item(session, db_sample)

    # THEN the read_samples endpoint should return the sample in the right format
    response = client.get(samples_endpoint)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == 1
    assert Sample(**result[0])


def test_read_samples_for_case(
    session: sessionmaker,
    client: TestClient,
    db_case: SQLCase,
    db_sample: SQLSample,
    samples_endpoint: str,
    helpers: Type,
):
    """Test the endpoint that returns all samples for a given case name."""

    # GIVEN a case object saved in the database
    helpers.session_commit_item(session, db_case)

    # Which contains a sample
    helpers.session_commit_item(session, db_sample)

    # THEN the read_samples_for_case endpoint should return the sample
    url = f"/{db_case.name}{samples_endpoint}"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert Sample(**result[0])


def test_read_sample(
    session: sessionmaker,
    client: TestClient,
    db_case: SQLCase,
    db_sample: SQLSample,
    samples_endpoint: str,
    helpers: Type,
):
    """Test the endpoint that returns a single sample when providing its name."""

    # GIVEN a case object saved in the database
    helpers.session_commit_item(session, db_case)

    # Which contains a sample
    helpers.session_commit_item(session, db_sample)

    # THEN the read_sample endpoint should return the sample
    url = f"{samples_endpoint}{db_sample.name}"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert Sample(**result)
