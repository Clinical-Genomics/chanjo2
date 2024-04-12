from copy import deepcopy
from typing import Type

from fastapi import status
from fastapi.testclient import TestClient
from requests.models import Response

from chanjo2.constants import GENE_LISTS_NOT_SUPPORTED_MSG
from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA, DEMO_COVERAGE_QUERY_FORM


def test_demo_report(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the coverage report for the demo sample."""

    # GIVEN a query to the demo report endpoint
    response: Response = client.get(endpoints.REPORT_DEMO)

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "report.html"


def test_report_request_no_genes(client: TestClient, endpoints: Type):
    """Test error handling when user tries to create a coverage report without providing a list of genes."""

    # GIVEN a request without a list of genes of interest
    REPORT_QUERY_NO_GENES: dict = deepcopy(DEMO_COVERAGE_QUERY_DATA)
    REPORT_QUERY_NO_GENES.pop("hgnc_gene_symbols")

    # GIVEN a query with json data to the report endpoint
    response: Response = client.post(
        endpoints.REPORT,
        json=REPORT_QUERY_NO_GENES,
    )

    # THEN the response should return the expected error code and message
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    result = response.json()
    assert GENE_LISTS_NOT_SUPPORTED_MSG in result["detail"]


def test_report_json_data(client: TestClient, endpoints: Type):
    """Test the coverage report endpoint by providing json data in a POST request."""

    # GIVEN a query with json data to the report endpoint
    response: Response = client.post(
        endpoints.REPORT,
        json=DEMO_COVERAGE_QUERY_DATA,
    )

    # THEN the request should be successful
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
