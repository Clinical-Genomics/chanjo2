from typing import List, Tuple


def parse_bed(bed_file: bytes) -> List[Tuple[str, int, int]]:
    """Parses a bed file containing genomic coordinates."""
    intervals: List[Tuple[str, int, int]] = []
    for line_byte in bed_file.rsplit(b"\n"):
        if len(line_byte) > 0 and not line_byte.startswith(b"#"):
            intervals.append(bed_line_to_region(bytes_line=line_byte))
    return intervals


def bed_line_to_region(bytes_line: bytes) -> Tuple[str, int, int]:
    """Returns a single genomic interval corresponding to a bed file line."""
    line_elements: List = bytes_line.decode("utf-8").rsplit("\t")
    return (line_elements[0], int(line_elements[1]), int(line_elements[2]))
