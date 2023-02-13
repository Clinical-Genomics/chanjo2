from pathlib import Path

import requests
from fastapi import status


def remote_resource_exists(resource_url: str) -> bool:
    """Checks that a coverage file hosted on a remote server exists."""
    try:
        response = requests.head(resource_url)
        return response.status_code == status.HTTP_200_OK
    except Exception as ex:
        return False


def local_resource_exists(resource_path: str) -> bool:
    """Checks that a coverage file hosted on the local disk exists."""
    return Path(resource_path).is_file()
