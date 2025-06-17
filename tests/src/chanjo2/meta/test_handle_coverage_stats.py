from chanjo2.meta.handle_coverage_stats import get_chromosomes_prefix


def test_get_chromosomes_prefix(
    real_coverage_path: str,
):
    """Test the function that extract the chromosome prefix (or lack of) from a d4 file."""

    # GIVEN a d4 file with no "chr" prefix
    # THEN the get_chromosomes_prefix function should return an empty string
    assert get_chromosomes_prefix(real_coverage_path) == ""
