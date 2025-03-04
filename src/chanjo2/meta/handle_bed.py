from typing import Iterator, List, Tuple

CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2


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
            line.rstrip().replace("chr", "").split("\t")
            for line in bed_file
            if line.startswith("#") is False
        ]

    interval_id_coords = []

    for interval in bed_file_contents:
        interval_id: str = (
            "_".join(interval[STOP_INDEX + 1 : len(interval)])
            if len(interval) > STOP_INDEX
            else f"{CHROM_INDEX}:{START_INDEX}-{STOP_INDEX}"
        )
        interval_coords: Tuple[str, int, int] = (
            interval[CHROM_INDEX],
            int(interval[START_INDEX]),
            int(interval[STOP_INDEX]),
        )
        interval_id_coords.append((interval_id, interval_coords))

    return interval_id_coords


def sort_interval_ids_coords(
    interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]],
) -> List[Tuple[str, Tuple[str, int, int]]]:
    """Sort intervals and their IDs by chrom, start and stop positions."""
    return sorted(
        interval_ids_coords,
        key=lambda interval_coord: (
            interval_coord[1][CHROM_INDEX],
            interval_coord[1][START_INDEX],
            interval_coord[1][STOP_INDEX],
        ),
    )
