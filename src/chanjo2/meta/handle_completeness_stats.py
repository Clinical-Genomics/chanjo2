import subprocess
import tempfile
from typing import Dict, List, Tuple

CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2


def get_d4tools_intervals_completeness(
    d4_file_path: str, bed_file_path: str, completeness_thresholds: List[int]
) -> List[Dict]:
    """Return coverage completeness over all intervals of a bed file using the perc_cov d4tools command."""
    threshold_stats = []
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
        threshold_stats.append(stats_dict)

    return threshold_stats


def get_completeness_stats(
    d4_file_path: str,
    thresholds: List[int],
    interval_ids_coords: List[Tuple[str, tuple]],
    chrom_prefix: str,
) -> Dict[str, dict]:
    """Compute coverage and completeness over the given intervals of a d4 file."""

    interval_id_completeness_stats: Dict[str:dict] = {}

    bed_lines = [
        f"{chrom_prefix}{coords[CHROM_INDEX]}\t{coords[START_INDEX]}\t{coords[STOP_INDEX]}"
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
        interval_id_completeness_stats[interval_id_coord[0]] = intervals_completeness[
            index
        ]

    return interval_id_completeness_stats
