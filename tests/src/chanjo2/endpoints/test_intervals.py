from typing import Tuple

from chanjo2.demo import d4_demo_path, gene_panel_path
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.models.pydantic_models import WRONG_COVERAGE_FILE_MSG
from fastapi import status
from fastapi.testclient import TestClient


def test_read_single_interval_d4_not_found(
    client: TestClient, coverage_file: str, interval_endpoint: str
):
    """Test the function that returns the coverage over an interval of a D4 file.
    Testing with a D4 file not found on disk or on a remote server."""

    # GIVEN one genomic interval of interest - first interval of a bed file
    interval: Tuple[str, int, int] = None
    with open(gene_panel_path, "rb") as f:
        contents = f.read()
        interval: Tuple[str, int, int] = parse_bed(contents)[0]

    # WHEN using the read_single_interval with a D4 not present on disk
    params = {
        "coverage_file_path": coverage_file,
        "chromosome": interval[0],
        "start": interval[1],
        "end": interval[2],
    }
    # THEN it should return 404 error
    response = client.get(interval_endpoint, params=params)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # WITH a meaningful message
    result = response.json()
    assert result["detail"] == WRONG_COVERAGE_FILE_MSG
