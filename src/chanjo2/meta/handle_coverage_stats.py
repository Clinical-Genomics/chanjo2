import subprocess
import tempfile
from collections import defaultdict
from typing import List, Optional, Tuple

from chanjo2.constants import CHROMOSOMES

CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2
STATS_MEAN_COVERAGE_INDEX = 3


def get_chromosomes_prefix(d4_file_path: str) -> str:
    """Extracts the prefix to be prepended to genomic intervals when calculating stats."""

    # SonarCloud: d4_file_path is validated upstream
    result = subprocess.run(
        ["d4tools", "view", "-g", d4_file_path],
        capture_output=True,
        text=True,
        check=True,
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else ""

    if "chr" in first_line:
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
    d4_file_path: str, chromosomes=List[str], bed_file_path: Optional[str] = None
) -> List[Tuple[str, float]]:
    """Return mean coverage over entire chromosomes."""

    if bed_file_path:
        chromosomes_stats_mean_cmd: List[str] = subprocess.check_output(
            [
                "d4tools",
                "stat",
                "--region",
                bed_file_path,
                d4_file_path,
                "--stat",
                "mean",
            ],
            text=True,
        ).splitlines()
    else:
        chromosomes_stats_mean_cmd: List[str] = subprocess.check_output(
            ["d4tools", "stat", "-s" "mean", d4_file_path],
            text=True,
        ).splitlines()

    total_cov = defaultdict(float)
    total_len = defaultdict(int)

    for line in chromosomes_stats_mean_cmd:
        stats_data = line.split("\t")
        chrom = stats_data[CHROM_INDEX]
        if chrom not in chromosomes:
            continue
        start = int(stats_data[START_INDEX])
        end = int(stats_data[STOP_INDEX])
        region_len = end - start
        mean_cov = float(stats_data[STATS_MEAN_COVERAGE_INDEX])

        total_cov[chrom] += mean_cov * region_len
        total_len[chrom] += region_len

    chromosomes_coverage = [
        (chrom, total_cov[chrom] / total_len[chrom])
        for chrom in chromosomes
        if total_len[chrom]
    ]

    return chromosomes_coverage
