import math
from statistics import mean
from typing import List, Union


def get_mean(float_list: List[float], round_by: int = 2) -> Union[float, str]:
    """Return the mean value from a list of floating point numbers, or a string when the value can't be converted to number."""

    clean_list = [x for x in float_list if not math.isnan(x)]

    if clean_list:
        mean_value = round(mean(clean_list), round_by)
    else:
        mean_value = "NA"

    return mean_value if str(mean_value).split(".")[0].isdigit() else str(mean_value)
