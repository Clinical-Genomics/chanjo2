import copy
import os
from typing import Callable, Type

import respx
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response as http_response
from requests.models import Response

from chanjo2.constants import HTTP_D4_COMPLETENESS_ERROR
from chanjo2.demo import DEMO_COVERAGE_QUERY_FORM, HTTP_SERVER_D4_file, d4_demo_path


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


@respx.mock
def test_report_form_data_auth_valid_token(
    auth_protected_client: TestClient,
    endpoints: Type,
    jwks_mock: dict,
    create_token: Callable,
):
    """Test the report endpoint with a non-valid access token."""

    # Mock the JWKS URL to return the JWKS public key set
    respx.get("http://localhost/.well-known/jwks.json").mock(
        return_value=http_response(200, json=jwks_mock)
    )

    # Create a valid token with the expected audience
    token = create_token("test-audience")
    # Set token in the test client cookies
    auth_protected_client.cookies.set("access_token", token)

    # Make a request to the protected endpoint
    response = auth_protected_client.post(
        endpoints.REPORT,  # Replace with your actual endpoint path
        data=DEMO_COVERAGE_QUERY_FORM,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Assert that access is authorized
    assert response.status_code == status.HTTP_200_OK


@respx.mock
def test_report_form_data_auth_invalid_token(
    auth_protected_client: TestClient,
    endpoints: Type,
    jwks_mock: dict,
    create_token: Callable,
):
    """Test the report endpoint with a non-valid access token."""

    # GIVEN a mocked response for the OIDC provider
    respx.get("http://localhost/.well-known/jwks.json").mock(
        return_value=http_response(200, json=jwks_mock)
    )

    # GIVEN a request with a token that is not valid
    token = create_token("wrong-audience")
    # Set token in the test client cookies
    auth_protected_client.cookies.set("access_token", token)

    response = auth_protected_client.post(
        endpoints.REPORT,
        data=DEMO_COVERAGE_QUERY_FORM,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # THEN the endpoint should return unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Token validation failed: Invalid audience"


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


def test_report_http_d4_with_completeness(client: TestClient, endpoints: Type):
    """Test model validation when a user sends a request to the report endpoint containing HTTP samples and completeness threshold."""

    # GIVEN one or more samples with HTTP d4 files present in the query
    query = copy.deepcopy(DEMO_COVERAGE_QUERY_FORM)
    query["samples"] = query["samples"].replace(d4_demo_path, HTTP_SERVER_D4_file)
    # WITH completeness thresholds
    assert query["completeness_thresholds"]

    # GIVEN a query with application/x-www-form-urlencoded data to the report endpoint
    response: Response = client.post(
        endpoints.REPORT,
        data=query,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # THEN the request should return error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # And return the expected validation error
    assert HTTP_D4_COMPLETENESS_ERROR in str(response.json())
