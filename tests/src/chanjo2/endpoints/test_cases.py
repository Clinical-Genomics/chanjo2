import copy
from typing import Dict, Type

from fastapi import status
from fastapi.testclient import TestClient

from chanjo2.models.pydantic_models import Case, Sample
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


def test_remove_case_with_sampke(
        client: TestClient,
        raw_case: Dict[str, str],
        raw_sample: Dict[str, str],
        coverage_path,
        endpoints: Type,
):
    """Test the endpoint that allows removing a case with a sample uniquely associated to this case using case name."""

    # GIVEN a database with a case
    client.post(endpoints.CASES, json=raw_case).json()
    assert (
            client.get(f"{endpoints.CASES}{raw_case['name']}").json()["name"]
            == raw_case["name"]
    )

    # AND a sample belonging to this case
    raw_sample["coverage_file_path"] = str(coverage_path)
    client.post(endpoints.SAMPLES, json=raw_sample)
    assert (
            client.get(f"{endpoints.SAMPLES}{raw_sample['name']}").json()["name"]
            == raw_sample["name"]
    )

    # GIVEN a request to delete the case
    url = f"{endpoints.CASES_DELETE}{raw_case['name']}"
    response = client.delete(url)
    # THEN the response should return success
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result == f"Removing case {raw_case['name']}. Affected rows: 1"

    # AND BOTH case and sample should be deleted
    result = client.get(f"{endpoints.CASES}{raw_case['name']}").json()
    assert result["detail"] == "Case not found"

    result = client.get(f"{endpoints.SAMPLES}{raw_sample['name']}").json()
    assert result["detail"] == "Sample not found"


def test_remove_case_shared_sample(
        client: TestClient,
        raw_case: Dict[str, str],
        raw_sample: Dict[str, str],
        coverage_path,
        endpoints: Type,
):
    """Test the endpoint that allows removing a case using its name when it shares a sample with other cases."""

    # GIVEN a database with 2 cases
    raw_case2: dict = copy.deepcopy(raw_case)
    CASE_2_NAME = "456"
    raw_case2["name"] = CASE_2_NAME
    for case in [raw_case, raw_case2]:
        client.post(endpoints.CASES, json=case).json()
        assert (
                client.get(f"{endpoints.CASES}{case['name']}").json()["name"]
                == case["name"]
        )

        # AND ONE sample associated with both
        raw_sample["case_name"] = case["name"]
        raw_sample["coverage_file_path"] = str(coverage_path)
        client.post(endpoints.SAMPLES, json=raw_sample)
        assert (
                client.get(f"{endpoints.SAMPLES}{raw_sample['name']}").json()["name"]
                == raw_sample["name"]
        )

    # THEN removing case 2
    url: str = f"{endpoints.CASES_DELETE}{CASE_2_NAME}"
    client.delete(url)
    result = client.get(f"{endpoints.CASES}{CASE_2_NAME}").json()
    assert result["detail"] == "Case not found"

    # SHOULD NOT remove shared sample
    result = client.get(f"{endpoints.SAMPLES}{raw_sample['name']}").json()
    assert Sample(**result)
