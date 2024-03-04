from typing import List, Tuple

from sqlalchemy.orm import sessionmaker

from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA
from chanjo2.meta.handle_report_contents import (
    get_missing_genes_from_db,
    get_report_data,
)
from chanjo2.models import SQLGene
from chanjo2.models.pydantic_models import ReportQuery

REPORT_EXPECTED_KEYS = [
    "levels",
    "extras",
    "completeness_rows",
    "incomplete_coverage_rows",
    "default_level_completeness_rows",
]
REPORT_EXPECTED_EXTRA_KEYS = [
    "panel_name",
    "default_level",
    "interval_type",
    "case_name",
    "hgnc_gene_ids",
    "build",
    "completeness_thresholds",
    "samples",
]


def test_get_missing_genes_from_db(
    demo_session: sessionmaker, demo_genes_37: List[SQLGene]
):
    """Test function that returns queried genes that are not present in the database."""

    # WHEN coverage query contains gene symbols that are not present in the database
    missing_gene_error: Tuple[str, List[Union[int, str]]] = get_missing_genes_from_db(
        sql_genes=demo_genes_37,
        hgnc_symbols=DEMO_COVERAGE_QUERY_DATA["hgnc_gene_symbols"],
    )

    # THEN the get_missing_genes_from_db function should return the expected error, containing description and missing IDs
    assert missing_gene_error[0] == "Gene IDs not found in the database"
    assert missing_gene_error[1]


def test_get_report_data(demo_session: sessionmaker):
    """Test the function that collects the deta required for creating a coverage/overview report."""

    # GIVEN a user query containing the expected parameters
    query = ReportQuery.parse_obj(DEMO_COVERAGE_QUERY_DATA)
    report_data: dict = get_report_data(query=query, session=demo_session)

    # THEN get_report_data should return a dictionary with the expected report info
    for expected_key in REPORT_EXPECTED_KEYS:
        assert expected_key in report_data

    for expected_key in REPORT_EXPECTED_EXTRA_KEYS:
        assert expected_key in report_data["extras"]
