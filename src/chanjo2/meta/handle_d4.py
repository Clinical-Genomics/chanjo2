from pathlib import Path

import requests


def local_resource_exists(resource_path: str) -> bool:
    """Checks that a coverage file hosted on the local disk exists."""
    return Path(resource_path).is_file()
