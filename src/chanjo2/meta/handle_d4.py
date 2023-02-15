from typing import Optional, Tuple

from pyd4 import D4File


def set_interval(
    chrom: str, start: Optional[int] = None, end: Optional[int] = None
) -> Tuple[str, Optional[int], Optional[int]]:
    """Create the interval tuple used by the pyd4 utility."""
    if start and end:
        return (chrom, start, end)
    return chrom


def set_d4_file(coverage_file_path: str) -> D4File:
    """Create a D4 file from a file path/URL."""
    return D4File(coverage_file_path)


def interval_coverage(
    d4_file: D4File, interval: Tuple[str, Optional[int], Optional[int]]
) -> float:
    """Return coverage over a single interval of a D4 file."""
    return d4_file.mean([interval])[0]
