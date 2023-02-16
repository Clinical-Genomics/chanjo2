from chanjo2.models.pydantic_models import WRONG_COVERAGE_FILE_MSG, CoverageInterval
from fastapi import status
from fastapi.testclient import TestClient


def test_read_single_interval_d4_not_found(
    client: TestClient, coverage_file: str, interval_endpoint: str, interval_query: dict
):
    """Test the function that returns the coverage over an interval of a D4 file.
    Testing with a D4 file not found on disk or on a remote server."""

    # WHEN using a query for a genomic interval with a D4 not present on disk
    interval_query["coverage_file_path"] = coverage_file

    # THEN a request to the read_single_interval should return 404 error
    response = client.get(interval_endpoint, params=interval_query)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # THEN show a meaningful message
    result = response.json()
    assert result["detail"] == WRONG_COVERAGE_FILE_MSG


def test_read_single_interval(
    client: TestClient,
    real_coverage_path: str,
    interval_endpoint: str,
    interval_query: dict,
):
    """Test the function that returns the coverage over an interval of a D4 file."""

    # WHEN using a query for the coverage over a genomic interval in a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path

    # THEN a request to the read_single_interval should be successful
    response = client.get(interval_endpoint, params=interval_query)
    assert response.status_code == status.HTTP_200_OK

    # AND the mean coverage over the interval should be returned
    result = response.json()
    coverage_data = CoverageInterval(**result)
    assert coverage_data.mean_coverage > 0
    # together with the queried interval
    assert coverage_data.chromosome
    assert coverage_data.start
    assert coverage_data.end


def test_read_single_chromosome(
    client: TestClient,
    real_coverage_path: str,
    interval_endpoint: str,
    interval_query: dict,
):
    """Test the function that returns the coverage over an entire chsomosome of a D4 file."""

    # GIVEN an interval query without start and and  coordinates
    interval_query.pop("start")
    interval_query.pop("end")

    # WHEN using the query for the coverage over a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path

    # THEN a request to the read_single_intervalshould be successful
    response = client.get(interval_endpoint, params=interval_query)
    assert response.status_code == status.HTTP_200_OK

    # AND the mean coverage over the entire chromosome should be present in the result
    result = response.json()
    coverage_data = CoverageInterval(**result)
    assert coverage_data.mean_coverage > 0
    # together with the queried interval
    assert coverage_data.chromosome
    assert coverage_data.start is None
    assert coverage_data.end is None
