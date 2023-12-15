from typing import Dict, List, Tuple

from sqlalchemy.orm import sessionmaker

from chanjo2.constants import DEFAULT_COMPLETENESS_LEVELS
from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA
from chanjo2.meta.handle_d4 import D4File, get_sample_interval_coverage
from chanjo2.meta.handle_report_contents import (
    get_gene_coverage_stats_by_interval,
    get_genes_overview_incomplete_coverage_rows,
    get_missing_genes_from_db,
    get_report_completeness_rows,
    get_report_level_completeness_rows,
)
from chanjo2.models import SQLGene, SQLTranscript

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


def test_get_genes_overview_incomplete_coverage_rows(
    demo_session: sessionmaker,
    samples_d4_list: List[Tuple[str, D4File]],
    demo_genes_37: List[SQLGene],
):
    """Test the function that returnes the lines of the genes coverage overview page."""

    # GIVEN coverage stats for a list of cases at the transcript level
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

    # THEN it should be possible to retrieve stats for the transcripts that are not fully covered at the given threshold
    genes_overview_lines: List[
        Tuple[Union[str, int, float]]
    ] = get_genes_overview_incomplete_coverage_rows(
        samples_coverage_stats=samples_coverage_stats,
        interval_type=SQLTranscript,
        cov_level=DEFAULT_COMPLETENESS_LEVELS[0],
    )

    # THEN each transcript line should contain the expected values
    for (
        gene_symbol,
        gene_hgnc_id,
        transcript_id,
        sample,
        completeness,
    ) in genes_overview_lines:
        assert isinstance(gene_symbol, str)
        assert isinstance(gene_hgnc_id, int)
        assert isinstance(transcript_id, str)
        assert sample == samples_d4_list[0][0]
        assert completeness < 1


def test_get_gene_coverage_stats_by_interval(
    demo_session: sessionmaker,
    samples_d4_list: List[Tuple[str, D4File]],
    demo_genes_37: List[SQLGene],
):
    """Tests the function that arranges samples coverage stats by inner interval."""

    # Given coverage stats by sample
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

    # WHEN passed to the get_gene_coverage_stats_by_interval function:
    intervals_coverage_stats: Dict[
        str, List[Tuple]
    ] = get_gene_coverage_stats_by_interval(coverage_by_sample=samples_coverage_stats)

    # THEN the returned data should have the expected format
    for interval_id, stats_tuples in intervals_coverage_stats.items():
        assert isinstance(interval_id, str)

        for stats_tuple in stats_tuples:
            assert isinstance(stats_tuple[0], str)  # sample name
            assert isinstance(stats_tuple[1], float)  # mean coverage
            assert isinstance(
                stats_tuple[2], dict
            )  # coverage completeness over threshoulds
