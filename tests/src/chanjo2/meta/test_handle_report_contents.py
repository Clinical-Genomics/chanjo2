from typing import List, Tuple, Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from chanjo2.constants import DEFAULT_COMPLETENESS_LEVELS
from chanjo2.crud.intervals import get_genes
from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA as query
from chanjo2.meta.handle_d4 import D4File
from chanjo2.meta.handle_d4 import get_sample_interval_coverage
from chanjo2.meta.handle_report_contents import get_report_level_completeness_rows
from chanjo2.models.sql_models import Transcript as SQLTranscript

DEFAULT_COVERAGE_LEVEL = 20


def test_get_report_level_completeness_rows(
    demo_session: sessionmaker,
    demo_client: TestClient,
    genomic_ids_per_build: Dict[str, List],
    samples_d4_list: List[Tuple[str, D4File]],
):
    """Test the function that report coverage completeness stats at the default level."""

    with demo_client:
        # GIVEN a list of genes present in the database
        gene_symbols = genomic_ids_per_build[query["build"]]["hgnc_symbols"]
        genes: List[SQLGene] = get_genes(
            db=demo_session,
            build=query["build"],
            ensembl_ids=[],
            hgnc_ids=[],
            hgnc_symbols=gene_symbols,
            limit=None,
        )
        assert genes

        # GIVEN coverage stats data on these genes:
        samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
            sample: get_sample_interval_coverage(
                db=demo_session,
                d4_file=d4_file,
                genes=genes,
                interval_type=SQLTranscript,
                completeness_thresholds=DEFAULT_COMPLETENESS_LEVELS,
            )
            for sample, d4_file in samples_d4_list
        }
        assert samples_coverage_stats

        # THEN it should be possible to retrieve stats for the default coverage level:
        default_level_samples_coverage_stats: List[
            Tuple[str, float, str]
        ] = get_report_level_completeness_rows(
            samples_coverage_stats=samples_coverage_stats, level=DEFAULT_COVERAGE_LEVEL
        )
        for (
            sample,
            mean_cov_intervals,
            not_covered_intervals,
        ) in default_level_samples_coverage_stats:
            assert isinstance(sample, str)
            assert isinstance(mean_cov_intervals, float) or mean_cov_intervals == 0
            assert isinstance(not_covered_intervals, str)
