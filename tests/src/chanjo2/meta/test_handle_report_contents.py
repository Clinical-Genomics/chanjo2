from typing import List, Tuple

from sqlalchemy.orm import sessionmaker

from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA
from chanjo2.meta.handle_report_contents import get_missing_genes_from_db
from chanjo2.models import SQLGene


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
