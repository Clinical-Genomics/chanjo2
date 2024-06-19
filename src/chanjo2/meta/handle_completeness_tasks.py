import subprocess
from multiprocessing import Manager, Pool
from typing import Dict, List, Tuple

INTERVAL_CHUNKS = 50
CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2
STATS_COVERAGE_INDEX = 3


def get_d4tools_coverage_completeness(
    d4_file_path: str,
    thresholds: List[int],
    return_dict: dict,
    interval_ids_coords: List[Tuple[str, tuple]],
):
    """Return the coverage completeness for the specified intervals of a d4 file."""
    for interval_id, coords in interval_ids_coords:

        bedgraph_coverage_contents: List[str] = subprocess.check_output(
            ["d4tools", "view", d4_file_path, f"{coords[0]}:{coords[1]}-{coords[2]}"],
            text=True,
        ).splitlines()

        bedgraph_stats = [line.split("\t") for line in bedgraph_coverage_contents]

        thresholds_dict = {}
        for threshold in thresholds:
            nr_bases_covered_above_threshold = 0

            for chrom_stats in bedgraph_stats:
                if int(chrom_stats[STATS_COVERAGE_INDEX]) >= threshold:
                    nr_bases_covered_above_threshold += int(
                        chrom_stats[STOP_INDEX]
                    ) - int(chrom_stats[START_INDEX])

            # Compute the fraction of bases covered above threshold
            thresholds_dict[threshold] = nr_bases_covered_above_threshold / (
                coords[STOP_INDEX] - coords[START_INDEX]
            )

        return_dict[interval_id] = thresholds_dict


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

    pool = Pool()
    pool.starmap_async(
        get_d4tools_coverage_completeness, [task for task in tasks_params]
    )

    pool.close()
    pool.join()

    return return_dict
