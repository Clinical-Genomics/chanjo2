from chanjo2.constants import DEFAULT_COMPLETENESS_LEVELS
from chanjo2.meta.handle_d4 import predict_sex
from chanjo2.models.pydantic_models import Sex
from chanjo2.meta.handle_d4 import get_intervals_completeness, get_d4_file
from pyd4 import D4File


def test_predict_sex_male():
    """Test the function that computes sex from coverage data from coverage file of a male sample."""
    # GIVEN a coverage of chromosome Y which is roughly half of chromosome X
    # THEN the predicted sex should be Male
    assert predict_sex(x_cov=12.568, y_cov=6.605) == Sex.MALE


def test_predict_sex_female():
    """Test the function that computes sex from coverage data from coverage file of a female sample."""
    # GIVEN a coverage of chromosome Y almost null
    # THEN the predicted sex should be female
    assert predict_sex(x_cov=22.81, y_cov=0.007) == Sex.FEMALE


def test_predict_sex_unknown():
    """Test the function that computes sex from coverage when it is not possible to establish the sex."""
    # GIVEN a coverage of chromosome X equal to 0
    # THEN the predicted sex should be unknown
    assert predict_sex(x_cov=0, y_cov=6.605) == Sex.UNKNOWN


def test_get_intervals_completeness_no_thresholds(real_coverage_path, bed_interval):
    """Test the get_intervals_completeness function when no coverage thresholds are specified."""
    # GIVEN a real d4 file
    d4_file: D4File = get_d4_file(real_coverage_path)

    # WHEN the get_intervals_completeness is invoked without completeness_thresholds values
    completeness_stats: Optional[dict] = get_intervals_completeness(
        d4_file=d4_file, intervals=[bed_interval], completeness_thresholds=None
    )

    # THEN it should return None
    assert completeness_stats is None


def test_get_intervals_completeness(real_coverage_path, bed_interval):
    """Test the function that returns coverage completeness over a d4 file for a list of intervals and a list of coverage thresholds."""

    # GIVEN a real d4 file
    d4_file: D4File = get_d4_file(real_coverage_path)

    # WHEN the get_intervals_completeness is invoked with all expected parameters
    completeness_stats: Dict[int, Decimal] = get_intervals_completeness(
        d4_file=d4_file,
        intervals=[bed_interval],
        completeness_thresholds=DEFAULT_COMPLETENESS_LEVELS,
    )
    # THEN it should return a dictionary
    assert isinstance(completeness_stats, dict)

    # CONTAINING stats for all the provided coverage thresholds
    for level in DEFAULT_COMPLETENESS_LEVELS:
        assert completeness_stats[level] == 0 or isinstance(
            completeness_stats[level], float
        )
