from chanjo2.demo import HTTP_SERVER_D4_file
from chanjo2.meta.handle_coverage_stats import get_chromosomes_prefix
from chanjo2.meta.handle_d4 import is_valid_url, predict_sex
from chanjo2.models.pydantic_models import Sex


def test_is_valid_url_false():
    """Test the function that checks if a string is formatted as a URL. Use a malformed URL."""
    assert is_valid_url("https://somefile") is False


def test_is_valid_url_true():
    """Test the function that checks if a string is formatted as a URL. Use a valid URL."""
    assert is_valid_url(HTTP_SERVER_D4_file)


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


def test_get_chromosomes_prefix_empty(real_coverage_path):
    """Test the function that retrieves the suffix to prepend to the intervals based on the metadata of a d4 file."""
    chr_prefix: str = get_chromosomes_prefix(real_coverage_path)
    assert chr_prefix == ""
