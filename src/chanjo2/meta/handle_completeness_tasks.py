import logging
import subprocess
import tempfile
from typing import Dict, List, Tuple

INTERVAL_CHUNKS = 50
CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2
STATS_COVERAGE_INDEX = 3
LOG = logging.getLogger(__name__)


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


def get_d4tools_intervals_completeness(
    d4_file_path: str, bed_file_path: str, completeness_thresholds: List[int]
) -> List[Dict]:
    """Return coverage completeness over all intervals of a bed file."""
    covered_threshold_stats = []
    d4tools_stats_perc_cov: str = subprocess.check_output(
        [
            "d4tools",
            "stat",
            "-s",
            f"perc_cov={','.join(str(threshold) for threshold in completeness_thresholds)}",
            "--region",
            bed_file_path,
            d4_file_path,
        ],
        text=True,
    )
    for line in d4tools_stats_perc_cov.splitlines():
        stats_dict: Dict = dict(
            (
                zip(
                    completeness_thresholds,
                    [float(stat) for stat in line.rstrip().split("\t")[3:]],
                )
            )
        )
        covered_threshold_stats.append(stats_dict)

    return covered_threshold_stats


def coverage_completeness_multitasker(
    d4_file_path: str,
    thresholds: List[int],
    interval_ids_coords: List[Tuple[str, tuple]],
) -> Dict[str, dict]:
    """Compute coverage and completeness over the given intervals of a d4 file using multiprocessing."""

    return_dict: Dict[str:dict] = {}

    bed_lines = [
        f"{coords[CHROM_INDEX]}\t{coords[START_INDEX]}\t{coords[STOP_INDEX]}"
        for _, coords in interval_ids_coords
    ]
    # Write genomic intervals to a temporary file
    with tempfile.NamedTemporaryFile(mode="w") as intervals_bed:
        intervals_bed.write("\n".join(bed_lines))
        intervals_bed.flush()
        intervals_completeness = get_d4tools_intervals_completeness(
            d4_file_path=d4_file_path,
            bed_file_path=intervals_bed.name,
            completeness_thresholds=thresholds,
        )

    for index, interval_id_coord in enumerate(interval_ids_coords):
        return_dict[interval_id_coord[0]] = intervals_completeness[index]

    return return_dict
