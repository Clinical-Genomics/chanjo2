from typing import Type

from fastapi import status
from fastapi.testclient import TestClient
from requests.models import Response

from chanjo2.demo import DEMO_COVERAGE_QUERY_FORM


def test_demo_report(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the coverage report for the demo sample."""

    # GIVEN a query to the demo report endpoint
    response: Response = client.get(endpoints.REPORT_DEMO)

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "report.html"


def test_report_form_data(client: TestClient, endpoints: Type):
    """Test the coverage report endpoint by providing application/x-www-form-urlencoded data in a POST request."""

    # GIVEN a query with application/x-www-form-urlencoded data to the report endpoint
    response: Response = client.post(
        endpoints.REPORT,
        data=DEMO_COVERAGE_QUERY_FORM,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "report.html"


def test_report_form_data_no_genes(client: TestClient, endpoints: Type):
    """Test the coverage report endpoint by providing application/x-www-form-urlencoded data in a POST request.
    Make sure that report gets creates even if request is missing genes info."""

    # GIVEN a submitted form not containing any genes:
    coverage_query_form_no_genes = dict(DEMO_COVERAGE_QUERY_FORM)
    for key in ["ensembl_gene_ids", "hgnc_gene_ids", "hgnc_gene_symbols"]:
        coverage_query_form_no_genes.pop(key)

    # GIVEN a query with application/x-www-form-urlencoded data to the report endpoint
    response: Response = client.post(
        endpoints.REPORT,
        data=coverage_query_form_no_genes,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "report.html"
