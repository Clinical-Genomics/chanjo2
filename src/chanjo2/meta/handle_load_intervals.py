import logging
from typing import List, Tuple

from chanjo2.constants import GENES_FILE_HEADER
from chanjo2.models.pydantic_models import Builds, IntervalBase
from schug.load.biomart import EnsemblBiomartClient
from schug.load.ensembl import fetch_ensembl_genes
from schug.load.fetch_resource import stream_resource

LOG = logging.getLogger("uvicorn.access")


async def resource_lines(url) -> Tuple[List[List], List]:
    """Returns header and lines of a downloaded resources as strings."""
    all_lines: List = "".join([i.decode("utf-8") async for i in stream_resource(url=url)]).split(
        "\n"
    )
    resource_header = all_lines[0]
    resource_lines = all_lines[1:-2]  # last 2 lines don't contain data
    return resource_header.split("\t"), resource_lines


def _ensembl_genes_url(build: Builds) -> str:
    """Return the URL to download genes using the Ensembl Biomart."""
    shug_client: EnsemblBiomartClient = fetch_ensembl_genes(build=build)
    return shug_client.build_url(xml=shug_client.xml)


async def update_genes(build: Builds) -> int:
    """Loads genes into the database."""
    LOG.info(f"Loading gene intervals. Genome build --> {build}")

    url: str = _ensembl_genes_url(build)
    header, lines = await resource_lines(url)
    if header != GENES_FILE_HEADER:
        LOG.warning(
            f"Ensembl genes file has an unexpected format:{header}. Expected format: {GENES_FILE_HEADER}"
        )
        return 0

    for line in lines:
        items = line.split("\t")
        # Load gene interval into the database
        interval: IntervalBase = IntervalBase(chromosome=items[0], start=items[1], stop=items[2])
        LOG.warning(interval.__dict__)
        # Create and link gene tags -> "gene", "ensembl_id", "hgnc symbol", "hgnc id"

    return 0
