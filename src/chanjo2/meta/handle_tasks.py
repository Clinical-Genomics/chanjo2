import logging
from typing import Dict, List, Tuple
from chanjo2.models.pydantic_models import ReportQuery, IntervalType
from itertools import chain
from statistics import mean

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


def report_stats_multitasker(
    query: ReportQuery,
    gene_intervals_coords: Dict[str, List[Tuple[str, int, int]]],
    report_data=dict,
):
    """Compute coverage and completeness over genomic intervals for a list of samples."""

    manager = Manager()
    temp_stats_dict = manager.dict()

    all_intervals: List[Tuple[str, int, int]] = list(
        chain(*gene_intervals_coords.values())
    )

    # Compute coverage over all intervals for all samples using multiprocessing (one sample per processor)
    parallel_coverage_tasks_by_sample = [
        (
            sample.coverage_file_path,
            [
                f"{tuple[CHROM_INDEX]}\t{tuple[START_INDEX]}\t{tuple[STOP_INDEX]}"
                for tuple in all_intervals
            ],
            temp_stats_dict,
            sample.name,
        )
        for sample in query.samples
    ]

    with Pool() as pool:
        pool.starmap(
            get_d4tools_intervals_mean_coverage, parallel_coverage_tasks_by_sample
        )

    temp_stats_dict = dict(temp_stats_dict)

    report_data["completeness_rows"] = []
    # report_data["default_level_completeness_rows"] = []
    for sample in query.samples:

        # Compute coverage completeness for this samples using multiprocessing (250 intervals per processor
        sample_completeness_stats: dict = dict(
            coverage_completeness_multitasker(
                d4_file_path=sample.coverage_file_path,
                thresholds=query.completeness_thresholds,
                interval_ids_coords=[
                    (
                        f"{interval[CHROM_INDEX]}:{interval[START_INDEX]}-{interval[STOP_INDEX]}",
                        (
                            interval[CHROM_INDEX],
                            interval[START_INDEX],
                            interval[STOP_INDEX],
                        ),
                    )
                    for interval in all_intervals
                ],
            )
        )
        sample_stats = {
            "mean_coverage": mean(temp_stats_dict[sample.name]["intervals_coverage"])

        }

        nr_interval_above_custom_threshold = 0
        intervals_thresholds_stats = {f"completeness_{threshold}":[] for threshold in query.completeness_thresholds}
        for interval_nr, (ensembl_gene, gene_coords) in enumerate(gene_intervals_coords.items()):

            for coords in gene_coords:
                str_coords: str = f"{coords[0]}:{coords[1]}-{coords[2]}"
                for threshold in query.completeness_thresholds:
                    intervals_thresholds_stats[f"completeness_{threshold}"].append(sample_completeness_stats[str_coords][threshold])
        
        
        for threshold in query.completeness_thresholds:
            intervals_thresholds_stats[f"completeness_{threshold}"] = round(mean(intervals_thresholds_stats[f"completeness_{threshold}"])*100, 2)

        sample_stats.update(intervals_thresholds_stats)

        report_data["completeness_rows"].append((sample.name, sample_stats))
