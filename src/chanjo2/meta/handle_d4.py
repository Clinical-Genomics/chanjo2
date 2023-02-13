from chanjo2.models.pydantic_models import CoverageInterval
from pyd4 import D4File


def open_d4(file_path: str) -> D4File:
    """Opens a D4 file and returns it"""
    return D4File(file_path)


def single_interval_coverage(file_path: str, interval_id: tuple) -> int:
    """Returns the mean coverage over a single genomic interval"""
    file = open_d4(file_path)
    return file[(interval_id)].mean()
