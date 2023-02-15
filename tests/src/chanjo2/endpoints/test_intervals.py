from typing import Tuple

from chanjo2.demo import d4_demo_path, gene_panel_path
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.models.pydantic_models import WRONG_COVERAGE_FILE_MSG
from fastapi.testclient import TestClient


def test_read_single_interval_d4_not_found(client: TestClient, coverage_file: str):
    """Test the function that returns the coverage over an interval of a D4 file.
    Testing with a D4 file not found on disk or on a remote server."""

    # GIVEN a genomic interval of interest
    with open(gene_panel_path, "rb") as f:
        contents = f.read()

        interval: Tuple[str, int, int] = parse_bed(contents)[0]
    assert interval
