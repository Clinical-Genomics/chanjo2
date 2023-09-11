from typing import List, Tuple

from sqlalchemy.orm import sessionmaker

from chanjo2.constants import DEFAULT_COMPLETENESS_LEVELS
from chanjo2.crud.intervals import get_genes
from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA as query
from chanjo2.meta.handle_d4 import D4File
from chanjo2.meta.handle_d4 import get_sample_interval_coverage
from chanjo2.models.sql_models import Gene as SQLGene


def test_get_report_level_completeness_rows(
    session: sessionmaker, genomic_ids_per_build
):
    """Test the function that report coverage completeness stats at the default level."""

    samples_d4_files: List[Tuple[str, D4File]] = [
        (sample["name"], D4File(sample["coverage_file_path"]))
        for sample in query["samples"]
    ]
    gene_symbols = genomic_ids_per_build[query["build"]]["hgnc_symbols"]
    assert gene_symbols
    genes: List[SQLGene] = get_genes(
        db=session,
        build=query["build"],
        ensembl_ids=[],
        hgnc_ids=[],
        hgnc_symbols=gene_symbols,
        limit=None,
    )

    assert genes
    # Given complete coverage stats data for a demo report query:
    samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
        sample: get_sample_interval_coverage(
            db=session,
            d4_file=d4_file,
            genes=genes,
            interval_type=SQLGene,
            completeness_thresholds=DEFAULT_COMPLETENESS_LEVELS,
        )
        for sample, d4_file in samples_d4_files
    }

    assert samples_coverage_stats == "jsk"


def test_get_report_completeness_rows(session: sessionmaker):
    """Test the function that report coverage completeness stats at all threshold levels."""
    pass
