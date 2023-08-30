from chanjo2.constants import DEFAULT_COMPLETENESS_LEVELS
from chanjo2.meta.handle_report_contents import coverage_completeness_by_sample
from chanjo2.models.pydantic_models import CoverageInterval


def test_coverage_completeness_by_sample(raw_sample, coverage_intervals):
    """Test the function that creates the stats for the "Generally important metrics" table in the coverage report."""

    sample_name: str = raw_sample["name"]
    # GIVEN a list of coverage intervals
    for interval in coverage_intervals:
        assert isinstance(interval, CoverageInterval)

    # WHEN the function that arranges this data by sample and completeness level is invoked
    sample_coverage_completeness: Dict = coverage_completeness_by_sample(
        samples=[sample_name],
        coverage_completeness_intervals=coverage_intervals,
        levels=DEFAULT_COMPLETENESS_LEVELS,
    )

    # THEN the data should contain the mean coverage over all queried intervals
    samples_avg_coverage = sample_coverage_completeness[sample_name]["mean_coverage"]
    assert isinstance(samples_avg_coverage, float)

    # THEN the data should contain coverage completeness over all queried threshold levels
    for level in DEFAULT_COMPLETENESS_LEVELS:
        level_coverage_completeness = sample_coverage_completeness[sample_name][
            "complenetess_level_value"
        ][level]
        assert isinstance(level_coverage_completeness, float)
