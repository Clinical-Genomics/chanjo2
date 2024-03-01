import logging
import subprocess
import tempfile
from multiprocessing import Manager, Pool
from typing import Dict, List, Tuple

LOG = logging.getLogger("uvicorn.access")
INTERVAL_CHUNKS = 250
CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2
STATS_MEAN_COVERAGE_INDEX = 3


def get_d4tools_coverage_completeness(
    d4_file_path: str,
    thresholds: List[int],
    return_dict: dict,
    interval_ids_coords: List[Tuple[str, tuple]],
):
    """Return the coverage completeness for the specified intervals of a d4 file."""

    for interval_id, interval_coords in interval_ids_coords:

        # Create a temporary minified bedgraph file with the lines containing this specific genomic interval
        tmp_stats_file = tempfile.NamedTemporaryFile()
        with open(tmp_stats_file.name, "w") as stats_file:
            d4tools_view_cmd = subprocess.Popen(
                [
                    "d4tools",
                    "view",
                    d4_file_path,
                    f"{interval_coords[CHROM_INDEX]}:{interval_coords[START_INDEX]}-{interval_coords[STOP_INDEX]}",
                ],
                stdout=stats_file,
            )
            d4tools_view_cmd.wait()

            thresholds_dict = {}
            threshold_index = 0
            while threshold_index < len(thresholds):
                # Collect the size of the intervals for each line with coverage above this threshold

                filter_lines_above_threshold: str = (
                    f"awk '{{ if ($4 >= {thresholds[threshold_index]} ) {{ print $3-$2; }} }}' {tmp_stats_file.name}"
                )
                intervals_above_threshold_sizes = subprocess.check_output(
                    [filter_lines_above_threshold], shell=True, text=True
                )

                nr_bases_covered_above_threshold: int = sum(
                    [int(size) for size in intervals_above_threshold_sizes.splitlines()]
                )

                # Compute the fraction of bases covered above threshold
                thresholds_dict[thresholds[threshold_index]] = (
                    nr_bases_covered_above_threshold
                    / (interval_coords[STOP_INDEX] - interval_coords[START_INDEX])
                )

                threshold_index += 1
                stats_file.flush()
                stats_file.seek(0)

        return_dict[interval_id] = thresholds_dict
        LOG.warning(f"Return dict: {return_dict}")


def coverage_completeness_multitasker(
    d4_file_path: str,
    thresholds: List[int],
    interval_ids_coords: List[Tuple[str, tuple]],
) -> Dict[str, dict]:
    """Compute coverage and completeness over the given intervals of a d4 file using multiprocessing."""

    manager = Manager()
    return_dict = manager.dict()  # Used for storing results from the separate processes

    split_intervals: List[List[Tuple[str, Tuple[str, int, int]]]] = [
        interval_ids_coords[chunk_index : chunk_index + INTERVAL_CHUNKS]
        for chunk_index in range(0, len(interval_ids_coords), INTERVAL_CHUNKS)
    ]

    tasks_params = [
        (d4_file_path, thresholds, return_dict, intervals)
        for intervals in split_intervals
    ]

    with Pool() as pool:
        pool.starmap(get_d4tools_coverage_completeness, tasks_params)

    LOG.warning(f"Return dict: {return_dict}")

    return return_dict
