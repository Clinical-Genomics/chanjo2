from pathlib import PosixPath
from typing import Callable, Dict, List, Tuple, Type

import pytest
from _io import TextIOWrapper
from chanjo2.constants import WRONG_BED_FILE_MSG, WRONG_COVERAGE_FILE_MSG
from chanjo2.demo import gene_panel_file, gene_panel_path
from chanjo2.models.pydantic_models import Builds, CoverageInterval, Gene, Transcript
from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture
from schug.demo import (
    EXONS_37_FILE_PATH,
    EXONS_38_FILE_PATH,
    GENES_37_FILE_PATH,
    GENES_38_FILE_PATH,
    TRANSCRIPTS_37_FILE_PATH,
    TRANSCRIPTS_38_FILE_PATH,
)

BUILD_GENES_RESOURCE: List[Tuple[Builds, str]] = [
    (Builds.build_37, GENES_37_FILE_PATH),
    (Builds.build_38, GENES_38_FILE_PATH),
]

BUILD_TRANSCRIPTS_RESOURCE: List[Tuple[Builds, str]] = [
    (Builds.build_37, TRANSCRIPTS_37_FILE_PATH),
    (Builds.build_38, TRANSCRIPTS_38_FILE_PATH),
]

BUILD_EXONS_RESOURCE: List[Tuple[Builds, str]] = [
    (Builds.build_37, EXONS_37_FILE_PATH),
    (Builds.build_38, EXONS_38_FILE_PATH),
]


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
    client: TestClient,
    real_coverage_path: str,
    endpoints: Type,
    interval_query: dict,
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


@pytest.mark.parametrize("build, path", BUILD_GENES_RESOURCE)
def test_load_genes(
    build: str,
    path: str,
    client: TestClient,
    endpoints: Type,
    mocker: MockerFixture,
    file_handler: Callable,
):
    """Test the endpoint that adds genes to the database in a given genome build."""

    # GIVEN a patched response from Ensembl Biomart, via schug
    gene_lines: TextIOWrapper = file_handler(path)
    mocker.patch(
        "chanjo2.meta.handle_load_intervals.parse_resource_lines",
        return_value=gene_lines,
    )

    # GIVEN a number of genes contained in the demo file
    nr_genes = len(gene_lines[1])
    # WHEN sending a request to the load_genes with genome build
    response: Response = client.post(f"{endpoints.LOAD_GENES}{build}")
    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK
    # THEN all the genes should be loaded
    assert response.json()["detail"] == f"{nr_genes} genes loaded into the database"

    # WHEN sending a request to the "genes" endpoint
    response: Response = client.get(f"{endpoints.GENES}{build}")
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    # THEN the expected number of genes should be returned
    assert len(result) == nr_genes
    # AND the gene should have the right format
    assert Gene(**result[0])


@pytest.mark.parametrize("build, path", BUILD_TRANSCRIPTS_RESOURCE)
def test_load_transcripts(
    build: str,
    path: str,
    client: TestClient,
    endpoints: Type,
    mocker: MockerFixture,
    file_handler: Callable,
):
    """Test the endpoint that adds genes to the database in a given genome build."""

    # GIVEN a patched response from Ensembl Biomart, via schug
    transcript_lines: TextIOWrapper = file_handler(path)
    mocker.patch(
        "chanjo2.meta.handle_load_intervals.parse_resource_lines",
        return_value=transcript_lines,
    )

    # GIVEN a number of transcripts contained in the demo file
    nr_transcripts = len(transcript_lines[1])

    # WHEN sending a request to the load_genes with genome build
    response: Response = client.post(f"{endpoints.LOAD_TRANSCRIPTS}{build}")
    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK
    # THEN all transcripts should be loaded
    assert (
        response.json()["detail"]
        == f"{nr_transcripts} transcripts loaded into the database"
    )
    # WHEN sending a request to the "transcripts" endpoint
    response: Response = client.get(f"{endpoints.TRANSCRIPTS}{build}")
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    # THEN the expected number of transcripts should be returned
    assert len(result) == nr_transcripts
    # AND the transcript should have the right format
    assert Transcript(**result[0])


@pytest.mark.parametrize("build, path", BUILD_EXONS_RESOURCE)
def test_load_exons(
    build: str,
    path: str,
    client: TestClient,
    endpoints: Type,
    mocker: MockerFixture,
    file_handler: Callable,
):
    """Test the endpoint that adds exons to the database in a given genome build."""

    # GIVEN a patched response from Ensembl Biomart, via schug
    exons_lines: TextIOWrapper = file_handler(path)
    mocker.patch(
        "chanjo2.meta.handle_load_intervals.parse_resource_lines",
        return_value=exons_lines,
    )

    # GIVEN a number of exons contained in the demo file
    nr_exons = len(exons_lines[1])

    # WHEN sending a request to the load_genes with genome build
    response: Response = client.post(f"{endpoints.LOAD_EXONS}{build}")

    # THEN it should return success
    # assert response.status_code == status.HTTP_200_OK
    # THEN all exons should be loaded
    assert response.json()["detail"] == f"{nr_exons} exons loaded into the database"

    """
    # WHEN sending a request to the "transcripts" endpoint
    response: Response = client.get(f"{endpoints.TRANSCRIPTS}{build}")
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    # THEN the expected number of transcripts should be returned
    assert len(result) == nr_transcripts
    # AND the transcript should have the right format
    assert Transcript(**result[0])
    """
