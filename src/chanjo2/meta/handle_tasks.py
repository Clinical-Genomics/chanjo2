import logging
from typing import Dict

LOG = logging.getLogger("uvicorn.access")

from chanjo2.meta.handle_d4 import get_d4tools_coverage_completeness
from typing import List, Tuple
from multiprocessing import Manager, Pool


def coverage_completeness_multitasker(
    d4_file_path: str,
    thresholds: List[int],
    interval_ids_coords: List[Tuple[str, tuple]],
) -> Dict[str, dict]:
    """Compute coverage and completeness over the given intervals of a d4 file using multiprocessing."""

    manager = Manager()
    return_dict = manager.dict()  # Used for storing results from the separate processes

    split_intervals: List[List[Tuple[str, Tuple[str, int, int]]]] = [
        interval_ids_coords[i : i + 250]
        for i in range(0, len(interval_ids_coords), 250)
    ]
    tasks_params = [
        (d4_file_path, thresholds, return_dict, intervals)
        for intervals in split_intervals
    ]

    with Pool() as pool:
        pool.starmap(get_d4tools_coverage_completeness, tasks_params)

    return return_dict
