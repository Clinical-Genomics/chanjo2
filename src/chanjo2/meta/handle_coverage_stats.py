import subprocess
import tempfile
from typing import List, Tuple

from chanjo2.constants import CHROMOSOMES

CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2
STATS_MEAN_COVERAGE_INDEX = 3


def get_chromosomes_prefix(d4_file_path: str) -> str:
    """Extracts the prefix to be prepended to genomic intervals when calculating stats.
    Depends on the chromosomes format present on the d4 file..
    """
    chr1_stats = subprocess.check_output(
        f"d4tools view -g {d4_file_path} | head -n 1", text=True, shell=True
    )
    if "chr" in chr1_stats:
        return "chr"
    return ""


def get_d4tools_intervals_mean_coverage(
    d4_file_path: str, interval_ids_coords: List[Tuple[str, tuple]], chrom_prefix: str
) -> List[float]:
    """Return the mean value over a list of intervals of a d4 file."""

    if interval_ids_coords:
        bed_lines = [
            f"{chrom_prefix}{coords[CHROM_INDEX]}\t{coords[START_INDEX]}\t{coords[STOP_INDEX]}"
            for _, coords in interval_ids_coords
        ]
        # Write genomic intervals to a temporary file
        with tempfile.NamedTemporaryFile(mode="w") as intervals_bed:
            intervals_bed.write("\n".join(bed_lines))
            intervals_bed.flush()

            return get_d4tools_intervals_coverage(
                d4_file_path=d4_file_path, bed_file_path=intervals_bed.name
            )
    chromosomes_mean_cov = get_d4tools_chromosome_mean_coverage(
        d4_file_path=d4_file_path, chromosomes=CHROMOSOMES
    )

    return [chrom_cov[1] for chrom_cov in chromosomes_mean_cov]


def get_d4tools_intervals_coverage(
    d4_file_path: str, bed_file_path: str
) -> List[float]:
    """Return the coverage for intervals of a d4 file that are found in a bed file."""

    d4tools_stats_mean_cmd: str = subprocess.check_output(
        ["d4tools", "stat", "--region", bed_file_path, d4_file_path, "--stat", "mean"],
        text=True,
    )
    return [
        float(line.rstrip().split("\t")[3])
        for line in d4tools_stats_mean_cmd.splitlines()
    ]


def get_d4tools_chromosome_mean_coverage(
    d4_file_path: str, chromosomes=List[str]
) -> List[Tuple[str, float]]:
    """Return mean coverage over entire chromosomes."""

    chromosomes_stats_mean_cmd: List[str] = subprocess.check_output(
        ["d4tools", "stat", "-s" "mean", d4_file_path],
        text=True,
    ).splitlines()
    chromosomes_coverage: List[Tuple[str, float]] = []
    for line in chromosomes_stats_mean_cmd:
        stats_data: List[str] = line.split("\t")
        if stats_data[CHROM_INDEX] in chromosomes:
            chromosomes_coverage.append(
                (stats_data[CHROM_INDEX], float(stats_data[STATS_MEAN_COVERAGE_INDEX]))
            )
    return chromosomes_coverage
