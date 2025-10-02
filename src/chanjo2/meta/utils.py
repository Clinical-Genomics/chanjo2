import math
from statistics import mean
from typing import List, Union


def get_mean(float_list: List[float], round_by: int = 2) -> Union[float, str]:
    """Return the mean value from a list of floats, optionally rounded.
    Returns 'NA' if the list has no valid numbers."""

    # Filter out NaNs
    clean_list = [x for x in float_list if not math.isnan(x)]

    if not clean_list:
        return "NA"

    mean_value = mean(clean_list)

    # Round only if round_by is not None
    if round_by is not None:
        mean_value = round(mean_value, round_by)

    return mean_value
