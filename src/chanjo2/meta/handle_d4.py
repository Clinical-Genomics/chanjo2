import logging
from pathlib import Path

import requests

LOG = logging.getLogger("uvicorn.access")


def remote_resource_exists(resource_url: str) -> bool:
    """Checks that a coverage file hosted on a remote server exists.
    It checks that response has right headers without downloading the coverage file."""
    try:
        response = requests.head(resource_url)
        return response.headers["content-type"] == "application/octet-stream"

    except Exception as ex:
        return False


def local_resource_exists(resource_path: str) -> bool:
    """Checks that a coverage file hosted on the local disk exists."""
    return Path(resource_path).is_file()
