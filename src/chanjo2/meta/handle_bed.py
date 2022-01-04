from typing import List


def parse_bed(bed_file: bytes) -> List[tuple[str, int, int]]:
    regions: List[tuple[str, int, int]] = []
    for region_byte in bed_file.rsplit(b"\n"):
        if len(region_byte) > 0:
            regions.append(bed_line_to_region(bytes_line=region_byte))
    return regions


def bed_line_to_region(bytes_line: bytes) -> tuple[str, int, int]:
    chromosome, start, stop = bytes_line.decode("utf-8").rsplit("\t")
    return chromosome, int(start), int(stop)
