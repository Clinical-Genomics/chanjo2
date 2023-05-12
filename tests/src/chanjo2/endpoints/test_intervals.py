from typing import Dict, Iterator, List, Type

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture

from chanjo2.constants import MULTIPLE_PARAMS_NOT_SUPPORTED_MSG
from chanjo2.models.pydantic_models import (
    Builds,
    Exon,
    Gene,
    Transcript,
)
from chanjo2.populate_demo import (
    BUILD_GENES_RESOURCE,
    BUILD_TRANSCRIPTS_RESOURCE,
    BUILD_EXONS_RESOURCE,
)
from chanjo2.populate_demo import resource_lines

MOCKED_FILE_PARSER = "chanjo2.meta.handle_load_intervals.read_resource_lines"


@pytest.mark.parametrize("build, path", BUILD_GENES_RESOURCE)
def test_load_genes(
    build: str,
    path: str,
    client: TestClient,
    endpoints: Type,
    mocker: MockerFixture,
):
    """Test the endpoint that adds genes to the database in a given genome build."""

    # GIVEN a patched response from Ensembl Biomart, via schug
    gene_lines: Iterator = resource_lines(path)
    mocker.patch(
        MOCKED_FILE_PARSER,
        return_value=gene_lines,
    )

    # GIVEN a number of genes contained in the demo file
    nr_genes: int = len(list(resource_lines(path))) - 1

    # WHEN sending a request to the load_genes with genome build
    response: Response = client.post(f"{endpoints.LOAD_GENES}{build}")
    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK

    # THEN all the genes should be loaded
    assert response.json()["detail"] == f"{nr_genes} genes loaded into the database"

    # WHEN sending a request to the "genes" endpoint
    response: Response = client.post(endpoints.GENES, json={"build": build})
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    # THEN the expected number of genes should be returned
    assert len(result) == nr_genes
    # AND the gene should have the right format
    assert Gene(**result[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_genes_multiple_filters(
    build: str,
    client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test filtering gene intervals providing more than one filter."""

    # GIVEN a query with genome build and more than one gene ID:
    data = {
        "build": build,
        "ensembl_ids": genomic_ids_per_build[build]["ensembl_gene_ids"],
        "hgnc_ids": genomic_ids_per_build[build]["hgnc_ids"],
    }
    # WHEN sending a POST request to the genes endpoint with the query params above
    response: Response = client.post(endpoints.GENES, json=data)
    # THEN it should return HTTP 400 error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    result = response.json()
    assert result["detail"] == MULTIPLE_PARAMS_NOT_SUPPORTED_MSG


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_genes_by_ensembl_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database genes using a list of ensembl IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "genes" endpoint with a list of Ensembl IDs
    data = {
        "build": build,
        "ensembl_ids": genomic_ids_per_build[build]["ensembl_gene_ids"],
    }
    response: Response = demo_client.post(endpoints.GENES, json=data)
    # THEN the expected number of genes should be returned
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == len(genomic_ids_per_build[build]["ensembl_gene_ids"])
    assert Gene(**result[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_genes_by_hgnc_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database genes using a list of HGNC IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "genes" endpoint with a list of HGNC ids
    data = {
        "build": build,
        "hgnc_ids": genomic_ids_per_build[build]["hgnc_ids"],
    }
    response: Response = demo_client.post(endpoints.GENES, json=data)
    # THEN the expected number of genes should be returned
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == len(genomic_ids_per_build[build]["hgnc_ids"])
    assert Gene(**result[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_genes_by_hgnc_symbols(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database genes using a list of HGNC symbols."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "genes" endpoint with a list of HGNC symbols
    data = {
        "build": build,
        "hgnc_symbols": genomic_ids_per_build[build]["hgnc_symbols"],
    }
    response: Response = demo_client.post(endpoints.GENES, json=data)
    # THEN the expected number of genes should be returned
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert len(result) == len(genomic_ids_per_build[build]["hgnc_symbols"])
    assert Gene(**result[0])


@pytest.mark.parametrize("build, path", BUILD_TRANSCRIPTS_RESOURCE)
def test_load_transcripts(
    build: str,
    path: str,
    client: TestClient,
    endpoints: Type,
    mocker: MockerFixture,
):
    """Test the endpoint that adds genes to the database in a given genome build."""

    # GIVEN a patched response from Ensembl Biomart, via schug
    transcript_lines: Iterator = resource_lines(path)
    mocker.patch(
        MOCKED_FILE_PARSER,
        return_value=transcript_lines,
    )

    # GIVEN a number of transcripts contained in the demo file
    nr_transcripts: int = len(list(resource_lines(path))) - 1

    # WHEN sending a request to the load_genes with genome build
    response: Response = client.post(f"{endpoints.LOAD_TRANSCRIPTS}{build}")
    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK
    # THEN all transcripts should be loaded
    assert (
        response.json()["detail"]
        == f"{nr_transcripts} transcripts loaded into the database"
    )


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_transcripts_multiple_filters(
    build: str,
    client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test filtering transcript intervals providing more than one filter."""

    # GIVEN a query to "transcripts" enspoind with genome build and more than one ID:
    data = {
        "build": build,
        "ensembl_ids": genomic_ids_per_build[build]["ensembl_transcript_ids"],
        "ensembl_gene_ids": genomic_ids_per_build[build]["ensembl_gene_ids"],
    }
    # WHEN sending a POST request to the transcripts endpoint with the query params above
    response: Response = client.post(endpoints.TRANSCRIPTS, json=data)
    # THEN it should return HTTP 400 error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    result = response.json()
    assert result["detail"] == MULTIPLE_PARAMS_NOT_SUPPORTED_MSG


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_transcripts_no_filters(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that returns database transcripts without any filter."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "transcripts" endpoint
    data = {
        "build": build,
    }
    response: Response = demo_client.post(endpoints.TRANSCRIPTS, json=data)

    # THEN transcript documents should be returned
    assert response.status_code == status.HTTP_200_OK
    transcripts = response.json()
    assert Transcript(**transcripts[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_transcripts_by_ensembl_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database transcripts using a list of Ensembl IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "transcripts" endpoint with a list of Ensembl IDs
    data = {
        "build": build,
        "ensembl_ids": genomic_ids_per_build[build]["ensembl_transcript_ids"],
    }
    response: Response = demo_client.post(endpoints.TRANSCRIPTS, json=data)

    # THEN transcript documents should be returned
    assert response.status_code == status.HTTP_200_OK
    transcripts = response.json()
    assert Transcript(**transcripts[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_transcripts_by_ensembl_gene_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database transcripts using a list of Ensembl gene IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "transcripts" endpoint with a list of Ensembl gene IDs
    data = {
        "build": build,
        "ensembl_gene_ids": genomic_ids_per_build[build]["ensembl_gene_ids"],
    }
    response: Response = demo_client.post(endpoints.TRANSCRIPTS, json=data)

    # THEN transcript documents should be returned
    assert response.status_code == status.HTTP_200_OK
    transcripts = response.json()
    assert Transcript(**transcripts[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_transcripts_by_hgnc_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database transcripts using a list of HGNC gene IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "transcripts" endpoint with a list of HGNC gene IDs
    data = {
        "build": build,
        "hgnc_gene_ids": genomic_ids_per_build[build]["hgnc_ids"],
    }
    response: Response = demo_client.post(endpoints.TRANSCRIPTS, json=data)

    # THEN transcript documents should be returned
    assert response.status_code == status.HTTP_200_OK
    transcripts = response.json()
    assert Transcript(**transcripts[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_transcripts_by_hgnc_symbols(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database transcripts using a list of HGNC gene symbols."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "transcripts" endpoint with a list of HGNC gene symbols
    data = {
        "build": build,
        "hgnc_gene_symbols": genomic_ids_per_build[build]["hgnc_symbols"],
    }
    response: Response = demo_client.post(endpoints.TRANSCRIPTS, json=data)

    # THEN transcript documents should be returned
    assert response.status_code == status.HTTP_200_OK
    transcripts = response.json()
    assert Transcript(**transcripts[0])


@pytest.mark.parametrize("build, path", BUILD_EXONS_RESOURCE)
def test_load_exons(
    build: str,
    path: str,
    client: TestClient,
    endpoints: Type,
    mocker: MockerFixture,
):
    """Test the endpoint that adds exons to the database in a given genome build."""

    # GIVEN a patched response from Ensembl Biomart, via schug
    exons_lines: Iterator = resource_lines(path)
    mocker.patch(
        MOCKED_FILE_PARSER,
        return_value=exons_lines,
    )

    # GIVEN a number of exons contained in the demo file
    nr_exons: int = len(list(resource_lines(path))) - 1

    # WHEN sending a request to the load_genes with genome build
    response: Response = client.post(f"{endpoints.LOAD_EXONS}{build}")

    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK
    # THEN all exons should be loaded
    assert response.json()["detail"] == f"{nr_exons} exons loaded into the database"


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_exons_multiple_filters(
    build: str,
    client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test filtering exon intervals providing more than one filter."""

    # GIVEN a query to "exons" endpoint with genome build and more than one ID:
    data = {
        "build": build,
        "ensembl_ids": genomic_ids_per_build[build]["ensembl_exons_ids"],
        "ensembl_gene_ids": genomic_ids_per_build[build]["ensembl_gene_ids"],
    }
    # WHEN sending a POST request to the exons endpoint with the query params above
    response: Response = client.post(endpoints.EXONS, json=data)
    # THEN it should return HTTP 400 error
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    result = response.json()
    assert result["detail"] == MULTIPLE_PARAMS_NOT_SUPPORTED_MSG


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_exons_no_filters(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that returns exons without any filter."""
    # GIVEN a populated demo database
    # WHEN sending a request to the "exons" endpoint without any filter
    data = {
        "build": build,
    }
    response: Response = demo_client.post(endpoints.EXONS, json=data)

    # THEN exon documents should be returned
    assert response.status_code == status.HTTP_200_OK
    exons = response.json()
    assert Exon(**exons[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_exons_by_ensembl_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database exons using a list of Ensembl IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "exons" endpoint with a list of Ensembl IDs
    data = {
        "build": build,
        "ensembl_ids": genomic_ids_per_build[build]["ensembl_exons_ids"],
    }
    response: Response = demo_client.post(endpoints.EXONS, json=data)

    # THEN exon documents should be returned
    assert response.status_code == status.HTTP_200_OK
    exons = response.json()
    assert Exon(**exons[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_exons_by_ensembl_gene_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database exons using a list of Ensembl gene IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "exons" endpoint with a list of Ensembl gene IDs
    data = {
        "build": build,
        "ensembl_gene_ids": genomic_ids_per_build[build]["ensembl_gene_ids"],
    }
    response: Response = demo_client.post(endpoints.EXONS, json=data)

    # THEN exons documents should be returned
    assert response.status_code == status.HTTP_200_OK
    exons = response.json()
    assert Exon(**exons[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_exons_by_hgnc_ids(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database exons using a list of HGNC gene IDs."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "exons" endpoint with a list of HGNC gene IDs
    data = {
        "build": build,
        "hgnc_gene_ids": genomic_ids_per_build[build]["hgnc_ids"],
    }
    response: Response = demo_client.post(endpoints.EXONS, json=data)

    # THEN exon documents should be returned
    assert response.status_code == status.HTTP_200_OK
    exons = response.json()
    assert Exon(**exons[0])


@pytest.mark.parametrize("build", Builds.get_enum_values())
def test_exons_by_hgnc_symbols(
    build: str,
    demo_client: TestClient,
    endpoints: Type,
    genomic_ids_per_build: Dict[str, List],
):
    """Test the endpoint that filters database exons using a list of HGNC gene symbols."""

    # GIVEN a populated demo database
    # WHEN sending a request to the "exons" endpoint with a list of HGNC gene symbols
    data = {
        "build": build,
        "hgnc_gene_symbols": genomic_ids_per_build[build]["hgnc_symbols"],
    }
    response: Response = demo_client.post(endpoints.EXONS, json=data)

    # THEN transcript documents should be returned
    assert response.status_code == status.HTTP_200_OK
    exons = response.json()
    assert Exon(**exons[0])
