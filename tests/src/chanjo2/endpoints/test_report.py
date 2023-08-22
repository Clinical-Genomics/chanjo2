from typing import Type
from unittest.mock import patch

from fastapi.testclient import TestClient
from requests.models import Response

from chanjo2.demo import d4_demo_path
from chanjo2.endpoints.report import DEMO_COVERAGE_QUERY_DATA


@patch.dict(DEMO_COVERAGE_QUERY_DATA["samples"][0], {'coverage_file_path': d4_demo_path})
def test_demo_report(client: TestClient, endpoints: Type):
    """Test the endpoint that creates the coverage report for the demo sample."""

    # GIVEN a query to the demo report endpoint
    response: Response = client.get(endpoints.REPORT_DEMO)

    # Then the request should be successful
    assert response.status == status.HTTP_200_OK

    # And return an HTML page
    assert response.template.name == 'report.html'
