from chanjo2.meta.handle_d4 import predict_sex
from chanjo2.models.pydantic_models import Sex


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
