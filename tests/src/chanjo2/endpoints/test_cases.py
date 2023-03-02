from typing import Dict, Type

from chanjo2.models.pydantic_models import Case
from chanjo2.models.sql_models import Case as SQLCase
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


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
    client: TestClient,
    session: sessionmaker,
    db_case: SQLCase,
    endpoints: Type,
    helpers: Type,
):
    """Test the endpoint returning all cases found in the database."""

    # GIVEN a case object saved in the database
    helpers.session_commit_item(session, db_case)

    # THEN the read_cases endpoint should return the case
    response = client.get(endpoints.CASES)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == 1
    assert Case(**result[0])


def test_read_case(
    client: TestClient,
    session: sessionmaker,
    db_case: SQLCase,
    endpoints: Type,
    helpers: Type,
):
    """Test the endpoint that returns a specific case."""

    # GIVEN a case object saved in the database
    helpers.session_commit_item(session, db_case)

    # WHEN sending a GET request to retrieve the specific case using its name
    response = client.get(f"{endpoints.CASES}{db_case.name}")

    # THEN it should  return success
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # AND the case object should be returned as result
    assert Case(**result)
