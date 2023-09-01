import copy
from typing import Type, Dict, List

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from chanjo2.constants import (
    WRONG_COVERAGE_FILE_MSG,
    WRONG_BED_FILE_MSG,
    MULTIPLE_GENE_LISTS_NOT_SUPPORTED_MSG,
    AMBIGUOUS_SAMPLES_INPUT,
)
from chanjo2.demo import gene_panel_path
from chanjo2.models.pydantic_models import Builds, Sex, GeneCoverage, IntervalCoverage
from chanjo2.populate_demo import DEMO_SAMPLE, DEMO_CASE

COVERAGE_COMPLETENESS_THRESHOLDS: List[int] = [10, 20, 30]

BASE_COVERAGE_QUERY: Dict[str, str] = {
    "completeness_thresholds": COVERAGE_COMPLETENESS_THRESHOLDS,
}
SAMPLE_COVERAGE_QUERY: Dict[str, str] = copy.deepcopy(BASE_COVERAGE_QUERY)
SAMPLE_COVERAGE_QUERY["samples"] = [DEMO_SAMPLE["name"]]

CASE_COVERAGE_QUERY: Dict[str, str] = copy.deepcopy(BASE_COVERAGE_QUERY)
CASE_COVERAGE_QUERY["case"] = DEMO_CASE["name"]


def test_d4_interval_coverage_d4_not_found(
    client: TestClient, mock_coverage_file: str, endpoints: Type, interval_query: dict
):
    """Test the function that returns the coverage over an interval of a D4 file.
    Testing with a D4 file not found on disk or on a remote server."""

    # WHEN using a query for a genomic interval with a D4 not present on disk
    interval_query["coverage_file_path"] = mock_coverage_file

    # THEN a request to the read_single_interval should return 404 error
    response = client.post(endpoints.INTERVAL_COVERAGE, json=interval_query)
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
    real_coverage_path: str,
    client: TestClient,
    endpoints: Type,
    real_d4_query: Dict[str, str],
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


def test_d4_intervals_coverage(
    real_coverage_path: str,
    client: TestClient,
    endpoints: Type,
    real_d4_query: Dict[str, str],
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


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_gene_coverage_case_and_samples(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Make sure the gene coverage endpoint returns error when providing BOTH case name and sample list."""

    # GIVEN a gene coverage query containing BOTH case name AND sample list
    case_query: Dict[str, str] = copy.deepcopy(CASE_COVERAGE_QUERY)
    case_query["samples"] = [DEMO_SAMPLE["name"]]
    case_query["build"] = build
    case_query["ensembl_gene_ids"] = genomic_ids_per_build[build]["ensembl_gene_ids"]

    # THEN the response should return error
    response = demo_client.post(endpoints.SAMPLE_GENES_COVERAGE, json=case_query)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # WITH a meaningful message
    result = response.json()
    assert result["detail"][0]["msg"] == AMBIGUOUS_SAMPLES_INPUT


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_coverage_multiple_genes_lists(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the validation of the parameters passed to the sample coverage endpoints when multiple gene lists are passed."""

    # GIVEN a sample gene coverage query containing multiple gene lists (hgnc_gene_symbols and hgnc_gene_ids)
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["hgnc_gene_symbols"] = genomic_ids_per_build[build]["hgnc_symbols"]
    sample_query["hgnc_gene_ids"] = genomic_ids_per_build[build]["hgnc_ids"]

    # THEN the response should be return error
    response = demo_client.post(endpoints.SAMPLE_GENES_COVERAGE, json=sample_query)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # AND a meaningful message
    result = response.json()

    assert result["detail"][0]["msg"] == MULTIPLE_GENE_LISTS_NOT_SUPPORTED_MSG


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_gene_coverage_hgnc_symbols(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over multiple genes of a sample when a list of HGNC symbols is provided."""

    # GIVEN a sample gene coverage query containing HGNC gene symbols
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["hgnc_gene_symbols"] = genomic_ids_per_build[build]["hgnc_symbols"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_GENES_COVERAGE, json=sample_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_gene_coverage_hgnc_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over multiple genes of a sampl when a list of HGNC IDs is providede."""

    # GIVEN a sample gene coverage query containing HGNC IDs
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["hgnc_gene_ids"] = genomic_ids_per_build[build]["hgnc_ids"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_GENES_COVERAGE, json=sample_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List = response.json()
    for interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_gene_coverage_ensembl_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over multiple genes of a sample when a list of Enseml IDs is provided."""

    # GIVEN a sample gene coverage query containing Ensembl IDs
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["ensembl_gene_ids"] = genomic_ids_per_build[build]["ensembl_gene_ids"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_GENES_COVERAGE, json=sample_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_transcripts_coverage_hgnc_symbols(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over transcripts of multiple genes of a sample when a list of HGNC symbols is provided."""

    # GIVEN a sample transcript coverage query containing HGNC gene symbols
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["hgnc_gene_symbols"] = genomic_ids_per_build[build]["hgnc_symbols"]

    # THEN the response should be successful
    response = demo_client.post(
        endpoints.SAMPLE_TRANSCRIPTS_COVERAGE, json=sample_query
    )
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_transcripts_coverage_hgnc_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over transcripts of multiple genes of a sampl when a list of HGNC IDs is providede."""

    # GIVEN a sample transcript coverage query containing HGNC IDs
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["hgnc_gene_ids"] = genomic_ids_per_build[build]["hgnc_ids"]

    # THEN the response should be successful
    response = demo_client.post(
        endpoints.SAMPLE_TRANSCRIPTS_COVERAGE, json=sample_query
    )
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_transcripts_coverage_ensembl_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over transcripts of multiple genes of a sample when a list of Enseml IDs is provided."""

    # GIVEN a sample transcript coverage query containing Ensembl IDs
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["ensembl_gene_ids"] = genomic_ids_per_build[build]["ensembl_gene_ids"]

    # THEN the response should be successful
    response = demo_client.post(
        endpoints.SAMPLE_TRANSCRIPTS_COVERAGE, json=sample_query
    )
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_exons_coverage_hgnc_symbols(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over exons of multiple genes of a sample when a list of HGNC symbols is provided."""

    # GIVEN a sample transcript coverage query containing HGNC gene symbols
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["hgnc_gene_symbols"] = genomic_ids_per_build[build]["hgnc_symbols"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_EXONS_COVERAGE, json=sample_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_exons_coverage_hgnc_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over exons of multiple genes of a sampl when a list of HGNC IDs is providede."""

    # GIVEN a sample transcript coverage query containing HGNC IDs
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["hgnc_gene_ids"] = genomic_ids_per_build[build]["hgnc_ids"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_EXONS_COVERAGE, json=sample_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_samples_exons_coverage_ensembl_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the function that returns the coverage over exons of multiple genes of a sample when a list of Enseml IDs is provided."""

    # GIVEN a sample transcript coverage query containing Ensembl IDs
    sample_query: Dict[str, str] = copy.deepcopy(SAMPLE_COVERAGE_QUERY)
    sample_query["build"] = build
    sample_query["ensembl_gene_ids"] = genomic_ids_per_build[build]["ensembl_gene_ids"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_EXONS_COVERAGE, json=sample_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_case_genes_coverage(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    # GIVEN a case gene coverage query containing Ensembl gene IDs
    case_query: Dict[str, str] = copy.deepcopy(CASE_COVERAGE_QUERY)
    case_query["build"] = build
    case_query["ensembl_gene_ids"] = genomic_ids_per_build[build]["ensembl_gene_ids"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_GENES_COVERAGE, json=case_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_case_transcripts_coverage(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    # GIVEN a case transcripts coverage query containing Ensembl gene IDs
    case_query: Dict[str, str] = copy.deepcopy(CASE_COVERAGE_QUERY)
    case_query["build"] = build
    case_query["ensembl_gene_ids"] = genomic_ids_per_build[build]["ensembl_gene_ids"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_TRANSCRIPTS_COVERAGE, json=case_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_case_exons_coverage(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    # GIVEN a case exons coverage query containing Ensembl gene IDs
    case_query: Dict[str, str] = copy.deepcopy(CASE_COVERAGE_QUERY)
    case_query["build"] = build
    case_query["ensembl_gene_ids"] = genomic_ids_per_build[build]["ensembl_gene_ids"]

    # THEN the response should be successful
    response = demo_client.post(endpoints.SAMPLE_EXONS_COVERAGE, json=case_query)
    assert response.status_code == status.HTTP_200_OK

    # AND return coverage intervals data
    coverage_intervals: List[str, GeneCoverage] = response.json()
    for _, interval in coverage_intervals:
        assert GeneCoverage(**interval)
