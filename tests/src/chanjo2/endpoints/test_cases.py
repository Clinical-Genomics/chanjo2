CASES_ENDPOINT = "/cases/"
from fastapi import status


def test_create_case(client, test_case):
    """Test the endpoint used to create a new case"""
    # GIVEN a json-like object containing the new case data:
    case_data = test_case

    # WHEN the create_case endpoint is used to create the case
    response = client.post(CASES_ENDPOINT, json=case_data)

    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK

    # AND the case should have been saved correctly
    saved_case = response.json()
    for key, _ in case_data.items():
        assert saved_case[key] == case_data[key]


def test_read_cases(client, session, db_case):
    """Test the endpoint returning all cases found in the database"""

    # GIVEN a case object saved in the database
    session.add(db_case)
    session.commit()
    session.refresh(db_case)

    # THEN the read_cases endpoint should return it
    response = client.get(CASES_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == 1
    assert result[0]["name"] == db_case.name


def test_read_case(client, session, db_case):
    """Test the endpoint that returns a specific case"""

    # GIVEN a case object saved in the database
    session.add(db_case)
    session.commit()
    session.refresh(db_case)

    # WHEN sending a GET request to retrieve the specific case using its name
    response = client.get(f"{CASES_ENDPOINT}{db_case.name}")

    # THEN it should  return success
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # AND the case object should be returned as result
    assert result["name"] == db_case.name
