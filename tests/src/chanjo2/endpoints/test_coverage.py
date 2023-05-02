from pathlib import PosixPath
from typing import Type, Dict, List

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from chanjo2.constants import WRONG_COVERAGE_FILE_MSG, WRONG_BED_FILE_MSG
from chanjo2.demo import gene_panel_file, gene_panel_path
from chanjo2.models.pydantic_models import (
    CoverageInterval,
    Builds,
)
from chanjo2.populate_demo import DEMO_SAMPLE


def test_d4_interval_coverage_d4_not_found(
    client: TestClient, mock_coverage_file: str, endpoints: Type, interval_query: dict
):
    """Test the function that returns the coverage over an interval of a D4 file.
    Testing with a D4 file not found on disk or on a remote server."""

    # WHEN using a query for a genomic interval with a D4 not present on disk
    interval_query["coverage_file_path"] = mock_coverage_file

    # THEN a request to the read_single_interval should return 404 error
    response = client.get(endpoints.INTERVAL_COVERAGE, params=interval_query)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # THEN show a meaningful message
    result = response.json()
    assert result["detail"] == WRONG_COVERAGE_FILE_MSG


def test_d4_interval_coverage(
    client: TestClient,
    real_coverage_path: str,
    endpoints: Type,
    interval_query: dict,
):
    """Test the function that returns the coverage over an interval of a D4 file."""

    # WHEN using a query for the coverage over a genomic interval in a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path

    # THEN a request to the read_single_interval should be successful
    response = client.get(endpoints.INTERVAL_COVERAGE, params=interval_query)
    assert response.status_code == status.HTTP_200_OK

    # THEN the mean coverage over the interval should be returned
    result = response.json()
    coverage_data = CoverageInterval(**result)
    assert coverage_data.mean_coverage > 0

    # THEN the queried interval should also be present
    assert coverage_data.chromosome
    assert coverage_data.start
    assert coverage_data.end


def test_d4_interval_coverage_single_chromosome(
    client: TestClient, real_coverage_path: str, endpoints: Type, interval_query: dict
):
    """Test the function that returns the coverage over an entire chsomosome of a D4 file."""

    # GIVEN an interval query without start and and  coordinates
    interval_query.pop("start")
    interval_query.pop("end")

    # WHEN using the query for the coverage over a local D4 file
    interval_query["coverage_file_path"] = real_coverage_path

    # THEN a request to the read_single_intervalshould be successful
    response = client.get(endpoints.INTERVAL_COVERAGE, params=interval_query)
    assert response.status_code == status.HTTP_200_OK

    # AND the mean coverage over the entire chromosome should be present in the result
    result = response.json()
    coverage_data = CoverageInterval(**result)
    assert coverage_data.mean_coverage > 0
    # together with the queried interval
    assert coverage_data.chromosome
    assert coverage_data.start is None
    assert coverage_data.end is None


def test_d4_intervals_coverage_d4_not_found(
    mock_coverage_file: str, client: TestClient, endpoints: Type
):
    """Test the function that returns the coverage over multiple intervals of a D4 file.
    Testing with a D4 file not found on disk or on a remote server."""

    # GIVEN a valid BED file containing genomic intervals
    files = [
        ("bed_file", (gene_panel_file, open(gene_panel_path, "rb"))),
    ]

    # WHEN using a query for genomic intervals with a D4 not present on disk
    d4_query = {"coverage_file_path": mock_coverage_file}

    # THEN a request to the endpoint should return 404 error
    response = client.post(
        endpoints.INTERVALS_FILE_COVERAGE, params=d4_query, files=files
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # AND show a meaningful message
    result = response.json()

    assert result["detail"] == WRONG_COVERAGE_FILE_MSG


def test_d4_intervals_coverage_malformed_bed_file(
    bed_path_malformed: PosixPath,
    real_coverage_path: str,
    client: TestClient,
    endpoints: Type,
    real_d4_query: Dict[str, str],
):
    """Test the function that returns the coverage over multiple intervals of a D4 file.
    Testing with a BED file that is not correctly formatted."""

    # GIVEN a malformed BED file
    files = [
        ("bed_file", ("a_file.bed", open(bed_path_malformed, "rb"))),
    ]

    # THEN a request to the endpoint should return 404 error
    response = client.post(
        endpoints.INTERVALS_FILE_COVERAGE, params=real_d4_query, files=files
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # AND show a meaningful message
    result = response.json()

    assert result["detail"] == WRONG_BED_FILE_MSG


def test_d4_intervals_coverage(
    real_coverage_path: str,
    client: TestClient,
    endpoints: Type,
    real_d4_query: Dict[str, str],
):
    """Test the function that returns the coverage over multiple intervals of a D4 file."""

    # GIVEN a valid BED file containing genomic intervals
    files = [
        ("bed_file", (gene_panel_file, open(gene_panel_path, "rb"))),
    ]

    # THEN a request to the endpoint should return HTTP 200
    response = client.post(
        endpoints.INTERVALS_FILE_COVERAGE, params=real_d4_query, files=files
    )
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    result = response.json()
    for interval in result:
        assert CoverageInterval(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_gene_coverage_hgnc_symbols(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over multiple genomic intervals (genes) of a sample."""

    # GIVING a sample coverage query containing HGNC gene symbols
    data = {
        "sample_name": DEMO_SAMPLE["name"],
        "build": build,
        "hgnc_symbols": genomic_ids_per_build[build]["hgnc_symbols"],
    }

    # THEN the response should be successful
    response = demo_client.post(endpoints.INTERVALS_SAMPLE_COVERAGE, json=data)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    result = response.json()
    for interval in result:
        assert CoverageInterval(**interval)