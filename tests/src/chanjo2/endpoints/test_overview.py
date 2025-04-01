from typing import Dict, List, Type

from fastapi import status
from fastapi.testclient import TestClient
from requests.models import Response

from chanjo2.constants import (
    BUILD_37,
    BUILD_38,
    DEFAULT_COMPLETENESS_LEVELS,
    WRONG_COVERAGE_FILE_MSG,
)
from chanjo2.demo import DEMO_COVERAGE_QUERY_FORM, d4_demo_path


def test_demo_overview(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the genes coverage overview page for the demo sample."""

    # GIVEN a query to the demo genes coverage overview endpoint
    response: Response = client.get(endpoints.OVERVIEW_DEMO)

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "overview.html"


def test_overview_form_data(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the genes coverage overview page by providing application/x-www-form-urlencoded data in the POST request."""

    # GIVEN a query with application/x-www-form-urlencoded data to the genes coverage overview endpoint
    response: Response = client.post(
        endpoints.OVERVIEW,
        data=DEMO_COVERAGE_QUERY_FORM,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "overview.html"


def test_overview_form_data_d4_not_found(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the genes coverage overview page by providing a sample with a d4 file not found on disk."""

    # GIVEN a query with application/x-www-form-urlencoded data and a sample with no valid d4 file on disk
    data = DEMO_COVERAGE_QUERY_FORM.copy()
    data["samples"] = data["samples"].replace(d4_demo_path, "foo")

    response: Response = client.post(
        endpoints.OVERVIEW,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Then the request should be returning error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # And return the expected validation error
    assert WRONG_COVERAGE_FILE_MSG in str(response.json())


def test_gene_overview(
    client: TestClient, endpoints: Type, genomic_ids_per_build: Dict[str, List]
):
    """Test the endpoint that show coverage overview over the intervals of a single gene."""

    # GIVEN a POST request containing form data:
    form_data = {
        "build": BUILD_37,
        "completeness_thresholds": DEFAULT_COMPLETENESS_LEVELS,
        "hgnc_gene_id": genomic_ids_per_build[BUILD_37]["hgnc_ids"][0],
        "default_level": 10,
        "samples": str(DEMO_COVERAGE_QUERY_FORM["samples"]),
        "interval_type": "transcripts",
    }

    response: Response = client.post(
        endpoints.GENE_OVERVIEW,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "gene-overview.html"


def test_demo_mane_overview(client: TestClient, endpoints: Type):
    """Test the endpoint that shows coverage over the MANE transcripts of a list of genes."""

    # GIVEN a query to the demo genes coverage overview endpoint
    response: Response = client.get(endpoints.MANE_OVERVIEW_DEMO)

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "mane-overview.html"


def test_mane_overview(
    client: TestClient, endpoints: Type, genomic_ids_per_build: Dict[str, List]
):
    """Test the endpoint that shows coverage over the MANE transcripts for a custom list of genes."""

    # GIVEN a POST request containing form data:
    form_data = {
        "build": BUILD_38,
        "completeness_thresholds": DEFAULT_COMPLETENESS_LEVELS,
        "hgnc_gene_id": genomic_ids_per_build[BUILD_38]["hgnc_ids"],
        "samples": str(DEMO_COVERAGE_QUERY_FORM["samples"]),
        "interval_type": "transcripts",
    }

    # GIVEN a query to the mane overview endpoint
    response: Response = client.post(
        endpoints.MANE_OVERVIEW,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "mane-overview.html"
