from chanjo2.meta.utils import get_mean
from math import nan, inf

def test_get_mean_floats():
    """Test invoking the get_mean function with a list of floating point numbers."""

    # GIVEN a list of float numbers
    value_list = [12.81, 34.72, 22.53]

    # get_mean should return a float
    assert isinstance(get_mean(float_list=value_list), float)


def test_get_mean_inf():
    """Test invoking the get_mean function with a list of numbers that contains a non-number."""

    # GIVEN a list of floats and an inf
    value_list = [inf, 7, 45.22]

    # get_mean should return the 'inf' string
    assert get_mean(float_list=value_list) == "inf"


def test_get_mean_nan():
    """Test invoking the get_mean function with a list of numbers that contains a 'nan'."""

    # GIVEN a list of floats and an inf
    value_list = [nan, 7, 45.22]

    # get_mean should return a number
    result = get_mean(float_list=value_list)
    assert isinstance(result, float)
