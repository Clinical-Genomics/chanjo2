from typing import Iterator, List, Tuple

CHROM_COL = 0
START_COL = 1
STOP_COL = 2


def resource_lines(file_path: str) -> Iterator[str]:
    resource = open(file_path, "r", encoding="utf-8")
    lines: List = resource.readlines()
    lines: List = [line.rstrip("\n") for line in lines]
    return iter(lines)


def bed_file_interval_id_coords(
    file_path: str,
) -> List[Tuple[str, Tuple[str, int, int]]]:
    """Parses a bed file and returns interval ID (gene or interval name) and coordinates."""

    with open(file_path, "r") as bed_file:
        bed_file_contents: List[List[str]] = [
            line.rstrip().split("\t")
            for line in bed_file
            if line.startswith("#") is False
        ]

    interval_id_coords = []

    for interval in bed_file_contents:
        interval_id: str = (
            "_".join(interval[STOP_COL + 1 : len(interval)])
            if len(interval) > STOP_COL
            else f"{CHROM_COL}:{START_COL}-{STOP_COL}"
        )
        interval_coords: Tuple[str, int, int] = (
            interval[CHROM_COL],
            int(interval[START_COL]),
            int(interval[STOP_COL]),
        )
        interval_id_coords.append((interval_id, interval_coords))

    return interval_id_coords
