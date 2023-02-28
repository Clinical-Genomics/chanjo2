import time

from chanjo2.demo.populate_demo import load_demo_data
from chanjo2.main import app
from chanjo2.models.pydantic_models import Case
from fastapi.testclient import TestClient


def test_load_demo_data(cases_endpoint: str):
    """Test the function that adds demo data"""

    # GIVEN a client of a read demo app
    with TestClient(app) as client:
        # After the startup event
        time.sleep(1)
        # THEN the cases endpoint
        response = client.get(cases_endpoint)
        result: list = response.json()
        # SHOULD return 1 case
        assert len(result) == 1
        assert Case(**result[0])
