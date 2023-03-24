import logging
from typing import List, Tuple

from chanjo2.constants import GENES_FILE_HEADER
from chanjo2.crud.intervals import count_genes, create_db_gene
from chanjo2.models.pydantic_models import Builds, GeneBase
from chanjo2.models.sql_models import Gene as SQLGene
from schug.load.biomart import EnsemblBiomartClient
from schug.load.ensembl import fetch_ensembl_genes
from schug.load.fetch_resource import stream_resource
from sqlmodel import Session

LOG = logging.getLogger("uvicorn.access")


async def resource_lines(url) -> Tuple[List[List], List]:
    """Returns header and lines of a downloaded resource."""
    all_lines: List = "".join(
        [i.decode("utf-8") async for i in stream_resource(url=url)]
    ).split("\n")
    resource_header = all_lines[0]
    resource_lines = all_lines[1:-2]  # last 2 lines don't contain data
    return resource_header.split("\t"), resource_lines


def _ensembl_genes_url(build: Builds) -> str:
    """Return the URL to download genes using the Ensembl Biomart."""
    shug_client: EnsemblBiomartClient = fetch_ensembl_genes(build=build)
    return shug_client.build_url(xml=shug_client.xml)


async def update_genes(build: Builds, session: Session) -> int:
    """Loads genes into the database."""

    LOG.info(f"Loading gene intervals. Genome build --> {build}")
    initial_genes: int = count_genes(db=session)
    url: str = _ensembl_genes_url(build)
    header, lines = await resource_lines(url)
    if header != GENES_FILE_HEADER:
        LOG.warning(
            f"Ensembl genes file has an unexpected format:{header}. Expected format: {GENES_FILE_HEADER}"
        )
        return 0

    for line in lines:
        items = [
            None if i == "" else i for i in line.split("\t")
        ]  # Convert empty strings to None

        # Load gene interval into the database
        gene: Gene = GeneBase(
            build=build,
            chromosome=items[0],
            start=int(items[1]),
            stop=int(items[2]),
            ensembl_id=items[3],
            hgnc_symbol=items[4],
            hgnc_id=items[5],
        )
        create_db_gene(db=session, gene=gene)

    n_loaded_genes: int = count_genes(db=session) - initial_genes
    LOG.info(f"{n_loaded_genes} genes loaded into the database.")
    return n_loaded_genes
