from typing import Type

from fastapi import status
from fastapi.testclient import TestClient
from requests.models import Response


def test_demo_overview(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the genes coverage overview page for the demo sample."""

    # GIVEN a query to the demo overview endpoint
    response: Response = client.get(endpoints.OVERVIEW_DEMO)

    # Then the request should be successful
    assert response.status_code == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == "overview.html"
