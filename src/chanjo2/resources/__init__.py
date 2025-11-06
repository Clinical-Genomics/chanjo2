from importlib_resources import files

BASE_PATH: str = "chanjo2.resources"


def get_sex_chroms_bed_file(build: str, interval_type: str, prefix: str) -> str:
    """Return the appropriate XY BED file path given build, interval type, and chr prefix."""

    file_name = f"{prefix}XY_{interval_type}_{build}_noPAR.bed"
    return str(files(BASE_PATH).joinpath(file_name))
