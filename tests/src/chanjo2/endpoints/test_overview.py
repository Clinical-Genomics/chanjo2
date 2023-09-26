from typing import Type

from fastapi import status
from fastapi.testclient import TestClient
from requests.models import Response

from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA


def test_demo_overview(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the genes coverage overview page for the demo sample."""

    # GIVEN a query to the demo genes coverage overview endpoint
    response: Response = client.get(endpoints.OVERVIEW_DEMO)

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "overview.html"


def test_overview_json_data(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the genes coverage overview page by providing json data in POST request."""

    # GIVEN a query with json data to the genes coverage overview endpoint
    response: Response = client.post(
        endpoints.OVERVIEW,
        json=DEMO_COVERAGE_QUERY_DATA,
    )

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "overview.html"
