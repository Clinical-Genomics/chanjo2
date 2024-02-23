import logging
from itertools import chain
from typing import Dict, List, Tuple

from chanjo2.models.pydantic_models import IntervalType, ReportQuery

LOG = logging.getLogger("uvicorn.access")

from multiprocessing import Manager, Pool
from typing import List, Tuple

from chanjo2.meta.handle_d4 import (
    get_d4tools_coverage_completeness,
    get_d4tools_intervals_mean_coverage,
)

INTERVAL_CHUNKS = 250
CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2


def coverage_completeness_multitasker(
    d4_file_path: str,
    thresholds: List[int],
    interval_ids_coords: List[Tuple[str, tuple]],
) -> Dict[str, dict]:
    """Compute coverage completeness over the given intervals of a d4 file using multiprocessing."""

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

    return return_dict


def samples_coverage_completeness_multitasker(
    query: ReportQuery, gene_intervals_coords: Dict[str, List[Tuple[str, int, int]]]
):
    """Compute coverage completeness over genomic intervals for one or more samples using multiprocessing."""

    coverage_completeness_by_sample: dict[str, Dict[str, float]] = {}
    interval_ids_coords = []
    for ensembl_gene, interval_coords in gene_intervals_coords.items():
        for ensembl_id, coords in interval_coords:
            interval_id: str = f"{ensembl_gene}_{ensembl_id}"
            interval_ids_coords.append((interval_id, coords))

    for sample in query.samples:
        coverage_completeness_by_sample[sample.name] = dict(
            coverage_completeness_multitasker(
                d4_file_path=sample.coverage_file_path,
                thresholds=query.completeness_thresholds,
                interval_ids_coords=interval_ids_coords,
            )
        )

    return coverage_completeness_by_sample


def samples_coverage_multitasker(
    query: ReportQuery,
    gene_intervals_coords: Dict[str, List[Tuple[str, Tuple[str, int, int]]]],
) -> Dict[str, List[float]]:
    """Compute coverage over genomic intervals for one or more samples using multiprocessing."""

    manager = Manager()
    return_dict = manager.dict()  # Used for storing results from the separate processes

    all_intervals_coords: List[Tuple[str, int, int]] = []
    for gene, interval in gene_intervals_coords.items():
        for interval_id, interval_coords in interval:
            all_intervals_coords.append(interval_coords)

    # Each coverage computation for a sample is a distinct multiprocessing task running in parallel
    parallel_coverage_tasks_by_sample = [
        (
            sample.coverage_file_path,
            [
                f"{tuple[CHROM_INDEX]}\t{tuple[START_INDEX]}\t{tuple[STOP_INDEX]}"
                for tuple in all_intervals_coords
            ],
            return_dict,
            sample.name,
        )
        for sample in query.samples
    ]

    with Pool() as pool:
        pool.starmap(
            get_d4tools_intervals_mean_coverage, parallel_coverage_tasks_by_sample
        )

    return return_dict
