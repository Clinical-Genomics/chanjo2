from typing import Type

from fastapi import status
from fastapi.testclient import TestClient
from requests.models import Response

from chanjo2.constants import JSON_CONTENT_TYPE_HEADER
from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA


def test_demo_report(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the coverage report for the demo sample."""

    # GIVEN a query to the demo report endpoint
    response: Response = client.get(endpoints.REPORT_DEMO)

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "report.html"


def test_report_json_data(client: TestClient, endpoints: Type):
    """Test the coverage report endpoint by providing json data in POST request."""

    # GIVEN a query with json data to the report endpoint
    response: Response = client.post(
        endpoints.REPORT,
        headers={"Content-Type": JSON_CONTENT_TYPE_HEADER},
        json=DEMO_COVERAGE_QUERY_DATA,
    )

    # THEN the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "report.html"
