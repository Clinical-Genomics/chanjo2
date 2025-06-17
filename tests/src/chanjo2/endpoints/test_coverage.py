import copy
from typing import Callable, Dict, List, Type

import respx
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response as http_response
from pytest_mock.plugin import MockerFixture

from chanjo2.constants import (
    HTTP_D4_COMPLETENESS_ERROR,
    WRONG_BED_FILE_MSG,
    WRONG_COVERAGE_FILE_MSG,
)
from chanjo2.demo import (
    BUILD_37,
    DEMO_CASE,
    DEMO_HGNC_IDS,
    DEMO_SAMPLE,
    HTTP_SERVER_D4_file,
    gene_panel_path,
)
from chanjo2.models.pydantic_models import IntervalCoverage, Sex

COVERAGE_COMPLETENESS_THRESHOLDS: List[int] = [10, 20, 30]

BASE_COVERAGE_QUERY: Dict[str, str] = {
    "completeness_thresholds": COVERAGE_COMPLETENESS_THRESHOLDS,
}
SAMPLE_COVERAGE_QUERY: Dict[str, str] = copy.deepcopy(BASE_COVERAGE_QUERY)
SAMPLE_COVERAGE_QUERY["samples"] = [DEMO_SAMPLE["name"]]

CASE_COVERAGE_QUERY: Dict[str, str] = copy.deepcopy(BASE_COVERAGE_QUERY)
CASE_COVERAGE_QUERY["case"] = DEMO_CASE["name"]


def test_d4_interval_coverage_d4_not_found_on_disk(
    client: TestClient, mock_coverage_file: str, endpoints: Type, interval_query: dict
):
    """Test the function that returns the coverage over an interval of a D4 file.
    Testing with a D4 file not found on disk."""

    # WHEN using a query for a genomic interval with a D4 not present on disk
    interval_query["coverage_file_path"] = mock_coverage_file

    # THEN a request to the read_single_interval should return 404 error
    response = client.post(endpoints.INTERVAL_COVERAGE, json=interval_query)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # THEN show a meaningful message
    result = response.json()
    assert result["detail"] == WRONG_COVERAGE_FILE_MSG


def test_d4_interval_coverage_d4_not_found_on_http(
    client: TestClient, mock_coverage_file: str, endpoints: Type, interval_query: dict
):
    """Test the function that returns the coverage over an interval of a D4 file.
    Testing with a D4 file that should present on a remote server but is not."""

    # WHEN using a query for a genomic interval with a D4 not present on disk
    interval_query["coverage_file_path"] = "https://somefile"

    # THEN a request to the read_single_interval should return 404 error
    response = client.post(endpoints.INTERVAL_COVERAGE, json=interval_query)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # THEN show a meaningful message
    result = response.json()
    assert result["detail"] == WRONG_COVERAGE_FILE_MSG


def test_d4_interval_coverage_http_d4_with_completeness(
    client: TestClient, endpoints: Type, interval_query: dict
):
    """Test a query to the d4_interval_coverage endpoint by providing a remote d4 and completeness thresholds."""

    # GIVEN a query with completeness thresholds and an HTTP d4 file
    query = copy.deepcopy(interval_query)
    query["completeness_thresholds"] = COVERAGE_COMPLETENESS_THRESHOLDS
    query["coverage_file_path"] = HTTP_SERVER_D4_file

    # THEN the endpoint should return query validation error
    response = client.post(endpoints.INTERVAL_COVERAGE, json=query)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # WITH informative message
    result = response.json()
    assert result["detail"] == HTTP_D4_COMPLETENESS_ERROR


def test_d4_interval_coverage(
    client: TestClient,
    real_coverage_path: str,
    endpoints: Type,
    interval_query: dict,
):
    """Test the function that returns the coverage over an interval of a D4 file."""

    # WHEN using a query for the coverage over a genomic interval in a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path
    interval_query["completeness_thresholds"] = COVERAGE_COMPLETENESS_THRESHOLDS

    # THEN a request to the read_single_interval should be successful
    response = client.post(endpoints.INTERVAL_COVERAGE, json=interval_query)
    assert response.status_code == status.HTTP_200_OK

    # THEN the mean coverage over the interval should be returned
    result = response.json()

    coverage_data = IntervalCoverage(**result)
    assert coverage_data.mean_coverage

    # THEN mean coverage value should be returned
    assert coverage_data.mean_coverage > 0
    # THEN coverage completeness should be returned for each of the provided thresholds
    for cov_threshold in COVERAGE_COMPLETENESS_THRESHOLDS:
        assert coverage_data.completeness[str(cov_threshold)] > 0


@respx.mock
def test_d4_interval_coverage_auth_invalid_token(
    auth_protected_client: TestClient,
    real_coverage_path: str,
    endpoints: Type,
    interval_query: dict,
    jwks_mock: dict,
    create_token: Callable,
):
    """Test the function that returns the coverage over an interval of a D4 file. Situation where the endpoint expects auth token but token is NOT valid."""

    # Mock the JWKS URL to return the JWKS public key set
    respx.get("http://localhost/.well-known/jwks.json").mock(
        return_value=http_response(200, json=jwks_mock)
    )

    # WHEN using a query for the coverage over a genomic interval in a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path
    interval_query["completeness_thresholds"] = COVERAGE_COMPLETENESS_THRESHOLDS

    # GIVEN a request with authorization in the request headers, with a token that is not valid:
    token = create_token("wrong-audience")
    response = auth_protected_client.post(
        endpoints.INTERVAL_COVERAGE,
        json=interval_query,
        headers={"Authorization": f"Bearer {token}"},
    )

    # THEN the endpoint should return unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Token validation failed: Invalid audience"


@respx.mock
def test_d4_interval_coverage_auth_valid_token(
    auth_protected_client: TestClient,
    real_coverage_path: str,
    endpoints: Type,
    interval_query: dict,
    jwks_mock: dict,
    create_token: Callable,
):
    """Test the function that returns the coverage over an interval of a D4 file. Situation where the endpoint receives a valid auth token in the request headers."""

    # Mock the JWKS URL to return the JWKS public key set
    respx.get("http://localhost/.well-known/jwks.json").mock(
        return_value=http_response(200, json=jwks_mock)
    )

    # WHEN using a query for the coverage over a genomic interval in a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path
    interval_query["completeness_thresholds"] = COVERAGE_COMPLETENESS_THRESHOLDS

    # GIVEN a request with authorization in the request headers with a valid token:
    # Create a valid token with the expected audience
    token = create_token("test-audience")
    response = auth_protected_client.post(
        endpoints.INTERVAL_COVERAGE,
        json=interval_query,
        headers={"Authorization": f"Bearer {token}"},
    )

    # THEN a request to the read_single_interval should be successful
    assert response.status_code == status.HTTP_200_OK

    # THEN the mean coverage over the interval should be returned
    result = response.json()

    coverage_data = IntervalCoverage(**result)
    assert coverage_data.mean_coverage


def test_d4_interval_coverage_single_chromosome(
    client: TestClient, real_coverage_path: str, endpoints: Type, interval_query: dict
):
    """Test the function that returns the coverage over an entire chromosome of a D4 file."""

    # GIVEN an interval query without start and and  coordinates
    interval_query.pop("start")
    interval_query.pop("end")

    # WHEN using the query for the coverage over a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path

    # THEN a request to the read_single_intervalshould be successful
    response = client.post(endpoints.INTERVAL_COVERAGE, json=interval_query)
    assert response.status_code == status.HTTP_200_OK

    # AND the mean coverage over the entire chromosome should be present in the result
    result = response.json()
    coverage_data = IntervalCoverage(**result)
    assert coverage_data.mean_coverage


def test_d4_intervals_coverage_d4_not_found(
    mock_coverage_file: str, client: TestClient, endpoints: Type
):
    """Test the function that returns the coverage over multiple intervals of a d4 file.
    Testing with a D4 file not found on disk or on a remote server."""

    # WHEN using a query for genomic intervals with a D4 not present on disk
    d4_query = {
        "coverage_file_path": mock_coverage_file,
        "intervals_bed_path": gene_panel_path,
    }

    # THEN a request to the endpoint should return 404 error
    response = client.post(endpoints.INTERVALS_FILE_COVERAGE, json=d4_query)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # AND show a meaningful message
    result = response.json()

    assert result["detail"] == WRONG_COVERAGE_FILE_MSG


def test_d4_intervals_coverage_malformed_bed_file(
    real_coverage_path: str, client: TestClient, endpoints: Type
):
    """Test the function that returns the coverage over multiple intervals of a d4 file.
    Testing with a BED file that is not correctly formatted."""

    # GIVEN a query with the path to an existing d4 file
    d4_query = {
        "coverage_file_path": real_coverage_path,
        "intervals_bed_path": "not_existing_bed.bed",
    }

    # THEN a request to the endpoint should return 404 error
    response = client.post(endpoints.INTERVALS_FILE_COVERAGE, json=d4_query)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # AND show a meaningful message
    result = response.json()

    assert result["detail"] == WRONG_BED_FILE_MSG


def test_d4_intervals_coverage_http_d4_with_completeness(
    client: TestClient, endpoints: Type
):
    """Test a query to the d4_intervals_coverage endpoint by providing a remote d4 and completeness thresholds."""

    # GIVEN a query with completeness thresholds and an HTTP d4 file
    d4_query = {
        "coverage_file_path": HTTP_SERVER_D4_file,
        "intervals_bed_path": gene_panel_path,
        "completeness_thresholds": COVERAGE_COMPLETENESS_THRESHOLDS,
    }

    # THEN the endpoint should return query validation error
    response = client.post(endpoints.INTERVALS_FILE_COVERAGE, json=d4_query)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # WITH informative message
    result = response.json()
    assert result["detail"] == HTTP_D4_COMPLETENESS_ERROR


def test_d4_intervals_coverage(
    real_coverage_path: str,
    client: TestClient,
    endpoints: Type,
):
    """Test the function that returns the coverage over multiple intervals of a d4 file."""

    # GIVEN a query with a valid d4 file and a valid BED file containing genomic intervals
    d4_query = {
        "coverage_file_path": real_coverage_path,
        "intervals_bed_path": gene_panel_path,
        "completeness_thresholds": COVERAGE_COMPLETENESS_THRESHOLDS,
    }

    # THEN a request to the endpoint should return HTTP 200
    response = client.post(endpoints.INTERVALS_FILE_COVERAGE, json=d4_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return stats over the intervals
    coverage_intervals: List = response.json()
    for interval in coverage_intervals:
        coverage_data = IntervalCoverage(**interval)
        # Including mean coverage
        assert coverage_data.mean_coverage > 0
        # And coverage completeness for each of the specified thresholds
        for cov_threshold in COVERAGE_COMPLETENESS_THRESHOLDS:
            assert coverage_data.completeness[str(cov_threshold)] > 0


def test_d4_genes_coverage_summary_wrong_d4_file_path(
    mocker: MockerFixture,
    mock_coverage_file: str,
    client: TestClient,
    endpoints: Type,
    demo_sql_genes: List[dict],
):
    """Tests Test the function that returns condensed stats when the path to at least one of the provided d4 files is wrong."""

    # GIVEN a patched response from GENES
    mocker.patch(
        "chanjo2.endpoints.coverage.set_sql_intervals", return_value=demo_sql_genes
    )
    # WHERE the path to the coverage file doesn't correspond to a real file
    query = {
        "build": BUILD_37,
        "samples": [
            {"name": DEMO_SAMPLE["name"], "coverage_file_path": mock_coverage_file}
        ],
        "hgnc_gene_ids": DEMO_HGNC_IDS,
        "coverage_threshold": 10,
        "interval_type": "genes",
    }
    # GIVEN a query to the d4_genes_coverage_summary endpoint with the expected query
    response = client.post(endpoints.GENES_COVERAGE_SUMMARY, json=query)
    # THEN the request to the d4_genes_coverage_summary should return 404 error:
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_d4_genes_coverage_summary_http_d4_file(client: TestClient, endpoints: Type):
    """Tests Test the function that returns condensed stats when the path to at least one of the provided d4 files is wrong. It should not accept remove HTTP files."""

    # GIVEN a query with HTTP d4 files
    query = {
        "build": BUILD_37,
        "samples": [
            {"name": DEMO_SAMPLE["name"], "coverage_file_path": HTTP_SERVER_D4_file}
        ],
        "hgnc_gene_ids": DEMO_HGNC_IDS,
        "coverage_threshold": 10,
        "interval_type": "genes",
    }

    # THEN the endpoint should return query validation error
    response = client.post(endpoints.GENES_COVERAGE_SUMMARY, json=query)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # WITH informative message
    result = response.json()
    assert result["detail"] == HTTP_D4_COMPLETENESS_ERROR


def test_d4_genes_coverage_summary(
    mocker: MockerFixture,
    real_coverage_path: str,
    client: TestClient,
    endpoints: Type,
    demo_sql_genes: List[dict],
):
    """Test the function that returns condensed stats containing only sample's mean coverage and completeness above a default threshold."""

    # GIVEN a patched response from GENES
    mocker.patch(
        "chanjo2.endpoints.coverage.set_sql_intervals", return_value=demo_sql_genes
    )

    query = {
        "build": BUILD_37,
        "samples": [
            {"name": DEMO_SAMPLE["name"], "coverage_file_path": real_coverage_path}
        ],
        "hgnc_gene_ids": DEMO_HGNC_IDS,
        "coverage_threshold": 10,
        "interval_type": "genes",
    }
    # GIVEN a query to the d4_genes_coverage_summary endpoint with the expected query
    response = client.post(endpoints.GENES_COVERAGE_SUMMARY, json=query)

    # THEN the request should be successful
    assert response.status_code == status.HTTP_200_OK
    condensed_summary = response.json()
    # And return the expected data
    assert condensed_summary[DEMO_SAMPLE["name"]]["coverage_completeness_percent"] > 0
    assert condensed_summary[DEMO_SAMPLE["name"]]["mean_coverage"] > 0


def test_get_samples_predicted_sex(
    real_coverage_path: str,
    client: TestClient,
    endpoints: Type,
):
    """Test the function that returns coverage over sex chromosomes as well as predicted sex."""

    # GIVEN a query to the predicted_sex endpoint with the path to a d4 file
    response = client.get(
        f"{endpoints.GET_SAMPLES_PREDICTED_SEX}?coverage_file_path={real_coverage_path}"
    )

    # THEN the request should be successful
    assert response.status_code == status.HTTP_200_OK
    sex_info = response.json()

    # WITH mean coverage over the sex chromosomes
    assert isinstance(sex_info["x_coverage"], float)
    assert isinstance(sex_info["y_coverage"], float)

    # AND a predicted sex as a string
    assert sex_info["predicted_sex"] == Sex.FEMALE
