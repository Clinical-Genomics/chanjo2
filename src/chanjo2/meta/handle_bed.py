from typing import Iterator, List, Tuple


def resource_lines(file_path: str) -> Iterator[str]:
    resource = open(file_path, "r", encoding="utf-8")
    lines: List = resource.readlines()
    lines: List = [line.rstrip("\n") for line in lines]
    return iter(lines)


def parse_bed(bed_file_content: bytes) -> List[Tuple[str, int, int]]:
    """Parses a bed file containing genomic coordinates."""
    intervals: List[Tuple[str, int, int]] = []
    for line_byte in bed_file_content.rsplit(b"\n"):
        if len(line_byte) > 0 and not line_byte.startswith(b"#"):
            intervals.append(bed_line_to_region(bytes_line=line_byte))
    return intervals


def bed_line_to_region(bytes_line: bytes) -> Tuple[str, int, int]:
    """Returns a single genomic interval corresponding to a bed file line."""
    line_elements: List = bytes_line.decode("utf-8").rsplit("\t")
    return (line_elements[0], int(line_elements[1]), int(line_elements[2]))
