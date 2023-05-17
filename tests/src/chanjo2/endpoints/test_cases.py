from typing import Dict, Type

from fastapi import status
from fastapi.testclient import TestClient

from chanjo2.models.pydantic_models import Case
from chanjo2.populate_demo import DEMO_CASE


def test_create_case(client: TestClient, raw_case: Dict[str, str], endpoints: Type):
    """Test the endpoint used to create a new case."""
    # GIVEN a json-like object containing the new case data:
    case_data = raw_case

    # WHEN the create_case endpoint is used to create the case
    response = client.post(endpoints.CASES, json=case_data)

    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK

    # AND the saved data should be correct and compliant with a Case model
    result = response.json()

    assert Case(**result)


def test_read_cases(
    demo_client: TestClient,
    endpoints: Type,
):
    """Test the endpoint returning all cases found in the database."""

    # GIVEN a populated database
    # THEN the read_cases endpoint should return the case
    response = demo_client.get(endpoints.CASES)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == 1
    assert Case(**result[0])


def test_read_case(
    demo_client: TestClient,
    endpoints: Type,
):
    """Test the endpoint that returns a specific case."""

    # GIVEN a populated database
    # WHEN sending a GET request to retrieve the specific case using its name
    response = demo_client.get(f"{endpoints.CASES}{DEMO_CASE['name']}")

    # THEN it should  return success
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # AND the case object should be returned as result
    assert Case(**result).name == DEMO_CASE["name"]


def test_remove_case(demo_client: TestClient, endpoints: Type):
    """Test the endpoint that allows removing a case using its name."""

    # GIVEN a populated demo database
    # GIVEN a request to delete a demo case
    url = f"{endpoints.CASES_DELETE}{DEMO_CASE['name']}"
    response = demo_client.delete(url)
    # THEN the response should return success
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result == f"Removing case {DEMO_CASE['name']}. Affected rows: 1"
