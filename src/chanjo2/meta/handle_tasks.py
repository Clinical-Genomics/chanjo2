import logging
from functools import partial

LOG = logging.getLogger("uvicorn.access")

from chanjo2.meta.handle_d4 import get_d4tools_coverage_completeness
from typing import List, Tuple
from multiprocessing import Manager, Pool

def coverage_completeness_multitasker(d4_file_path: str, intervals: List[Tuple[str, int, int]], thresholds: List[int]):
    """Divide coverage completeness computation into multiple tasks to speed up server response."""

    pass
    """
    inarrays: List[Tuple[str , List[int]], List[Tuple[str, int, int]]] = [(d4_file_path, thresholds, intervals[i:i + 250]) for i in range(0, len(intervals), 250)]

    manager = multiprocessing.Manager()
    stats_dir: dict =  manager.dict()

    with Pool(processes=8) as pool:
        outarrays = pool.starmap(get_d4_intervals_completeness, inarrays)

    LOG.error(len(outarrays))
    counter = 0
    for outarray in outarrays:
        counter += len(outarray)
        LOG.warning(counter)


    return []
    """