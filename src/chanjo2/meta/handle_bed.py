import logging
from typing import List, Tuple

LOG = logging.getLogger("uvicorn.access")


def parse_bed(bed_file: bytes) -> List[Tuple[str, int, int]]:
    regions: List[tuple[str, int, int]] = []
    for region_byte in bed_file.rsplit(b"\n"):
        if len(region_byte) > 0 and not region_byte.startswith(b"#"):
            LOG.warning(region_byte)
            regions.append(bed_line_to_region(bytes_line=region_byte))
    return regions


def bed_line_to_region(bytes_line: bytes) -> Tuple[str, int, int]:
    line_elements: List = bytes_line.decode("utf-8").rsplit("\t")
    return line_elements[0], int(line_elements[1]), int(line_elements[2])
