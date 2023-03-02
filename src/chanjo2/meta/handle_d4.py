from typing import List, Optional, Tuple

from chanjo2.models.pydantic_models import CoverageInterval
from pyd4 import D4File


def set_interval(
    chrom: str, start: Optional[int] = None, end: Optional[int] = None
) -> Tuple[str, Optional[int], Optional[int]]:
    """Create the interval tuple used by the pyd4 utility."""
    return (chrom, start, end) if start and end else chrom


def set_d4_file(coverage_file_path: str) -> D4File:
    """Create a D4 file from a file path/URL."""
    return D4File(coverage_file_path)


def interval_coverage(
    d4_file: D4File, interval: Tuple[str, Optional[int], Optional[int]]
) -> float:
    """Return coverage over a single interval of a D4 file."""
    return d4_file.mean([interval])[0]


def intervals_coverage(
    d4_file: D4File, intervals: List[Tuple[str, int, int]]
) -> List[CoverageInterval]:
    """Return coverage over a list of intervals."""
    intervals_cov: List[CoverageInterval] = []
    for interval in intervals:
        intervals_cov.append(
            CoverageInterval(
                **{
                    "chromosome": interval[0],
                    "start": interval[1],
                    "end": interval[2],
                    "mean_coverage": d4_file.mean(interval),
                }
            )
        )
    return intervals_cov
