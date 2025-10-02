import math
from statistics import mean
from typing import List, Optional, Union


def get_mean(float_list: List[float], round_by: Optional[int] = 2) -> Union[float, str]:
    """Return the mean value from a list of floats, optionally rounded.
    Returns 'NA' if the list has no valid numbers.
    Converts inf/-inf to string 'inf'/'-inf'."""

    # Filter out NaNs
    clean_list = [x for x in float_list if not math.isnan(x)]

    if not clean_list:
        return "NA"

    mean_value = mean(clean_list)

    # Round only if round_by is not None
    if round_by is not None and math.isfinite(mean_value):
        mean_value = round(mean_value, round_by)

    # Convert infinities to strings
    if math.isinf(mean_value):
        return str(mean_value)

    return mean_value
