from typing import List, Tuple, Dict

from sqlalchemy.orm import sessionmaker

from chanjo2.constants import DEFAULT_COMPLETENESS_LEVELS
from chanjo2.meta.handle_d4 import D4File
from chanjo2.meta.handle_d4 import get_sample_interval_coverage
from chanjo2.meta.handle_report_contents import (
    get_report_level_completeness_rows,
    get_report_completeness_rows,
)
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript

DEFAULT_COVERAGE_LEVEL = 20


def test_get_report_level_completeness_rows(
    demo_session: sessionmaker,
    samples_d4_list: List[Tuple[str, D4File]],
    demo_genes_37: List[SQLGene],
):
    """Test the function that returns coverage completeness stats at the default level."""

    # GIVEN coverage stats for a list of cases
    samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
        sample: get_sample_interval_coverage(
            db=demo_session,
            d4_file=d4_file,
            genes=demo_genes_37,
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
        incompletely_covered_intervals,
        incompletely_covered_genes,
    ) in default_level_samples_coverage_stats:
        assert isinstance(sample, str)
        assert isinstance(mean_cov_intervals, float) or mean_cov_intervals == 0
        assert isinstance(incompletely_covered_intervals, str)
        assert isinstance(incompletely_covered_genes, list)


def test_get_report_completeness_rows(
    demo_session: sessionmaker,
    samples_d4_list: List[Tuple[str, D4File]],
    demo_genes_37: List[SQLGene],
):
    """Test the function that returns coverage completeness stats for a number of samples and different level thresholds.."""

    # GIVEN coverage stats for a list of cases
    samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
        sample: get_sample_interval_coverage(
            db=demo_session,
            d4_file=d4_file,
            genes=demo_genes_37,
            interval_type=SQLTranscript,
            completeness_thresholds=DEFAULT_COMPLETENESS_LEVELS,
        )
        for sample, d4_file in samples_d4_list
    }
    assert samples_coverage_stats

    # THEN completeness rows should contain the expected stats for each sample
    samples_completeness_rows: List[
        Tuple[str, Dict[str, float]]
    ] = get_report_completeness_rows(
        samples_coverage_stats=samples_coverage_stats,
        levels=DEFAULT_COMPLETENESS_LEVELS,
    )
    for sample, stats in samples_completeness_rows:
        assert sample == samples_d4_list[0][0]
        for level in DEFAULT_COMPLETENESS_LEVELS:
            assert f"completeness_{level}" in stats
