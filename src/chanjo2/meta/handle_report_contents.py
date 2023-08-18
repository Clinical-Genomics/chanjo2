import logging
from collections import OrderedDict
from typing import List

LOG = logging.getLogger("uvicorn.access")


def get_ordered_levels(threshold_levels: List[int]) -> OrderedDict:
    """Returns the coverage threshold levels as an ordered dictionary."""
    report_levels = OrderedDict()
    for threshold in sorted(threshold_levels, reverse=True):
        report_levels[threshold] = f"completeness_{threshold}"
    return report_levels
