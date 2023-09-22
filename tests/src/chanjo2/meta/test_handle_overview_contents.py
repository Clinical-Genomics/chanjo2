from typing import Dict, List, Tuple

from sqlalchemy.orm import sessionmaker

from chanjo2.constants import DEFAULT_COMPLETENESS_LEVELS
from chanjo2.meta.handle_d4 import D4File
from chanjo2.meta.handle_overview_content import (
    get_sample_interval_coverage,
    get_genes_overview_incomplete_coverage_rows,
)
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript


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
    for gene, transcript_id, sample, completeness in genes_overview_lines:
        assert isinstance(gene, str)
        assert isinstance(transcript_id, str)
        assert sample == samples_d4_list[0][0]
        assert completeness < 1
