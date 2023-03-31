import logging
from typing import List, Tuple

from chanjo2.constants import GENES_FILE_HEADER
from chanjo2.crud.intervals import (
    bulk_insert_genes,
    count_intervals_for_build,
    delete_intervals_for_build,
)
from chanjo2.models.pydantic_models import Builds, GeneBase
from chanjo2.models.sql_models import Gene as SQLGene
from schug.load.biomart import EnsemblBiomartClient
from schug.load.ensembl import fetch_ensembl_genes
from schug.load.fetch_resource import stream_resource
from schug.models.common import Build as SchugBuild
from sqlmodel import Session

LOG = logging.getLogger("uvicorn.access")


async def parse_resource_lines(url) -> Tuple[List[List[str]], List[str]]:
    """Returns header and lines of a downloaded resource."""
    all_lines: List[str] = "".join(
        [i.decode("utf-8") async for i in stream_resource(url=url)]
    ).split("\n")
    all_lines = [line.rstrip("\n") for line in all_lines]
    resource_header: str = all_lines[0]
    resource_lines: List[str] = all_lines[1:-2]  # last 2 lines don't contain data
    return resource_header.split("\t"), resource_lines


def _get_ensembl_genes_url(build: Builds) -> str:
    """Return the URL to download genes using the Ensembl Biomart."""
    shug_client: EnsemblBiomartClient = fetch_ensembl_genes(
        build=SchugBuild(build)
    )  # Schug converts 'GRCh38' to '38'
    return shug_client.build_url(xml=shug_client.xml)


async def update_genes(build: Builds, session: Session) -> Tuple[int, str]:
    """Loads genes into the database."""

    LOG.info(f"Loading gene intervals. Genome build --> {build}")

    url: str = _get_ensembl_genes_url(build)
    header, lines = await parse_resource_lines(url)

    if header != GENES_FILE_HEADER[build]:
        error = f"Ensembl genes file has an unexpected format:{header}. Expected format: {GENES_FILE_HEADER[build]}"
        LOG.error(error)
        return 0, error

    db_genes: List[SQLGene] = []
    for line in lines:
        items = [
            None if i == "" else i.replace("HGNC:", "") for i in line.split("\t")
        ]  # Convert empty strings to None
        # Load gene interval into the database
        gene: SQLGene = GeneBase(
            build=build,
            chromosome=items[0],
            start=int(items[1]),
            stop=int(items[2]),
            ensembl_id=items[3],
            hgnc_symbol=items[4],
            hgnc_id=items[5],
        )
        db_genes.append(gene)

    delete_intervals_for_build(db=session, interval_type=SQLGene, build=build)
    bulk_insert_genes(db=session, gene_list=db_genes)
    nr_loaded_genes: int = count_intervals_for_build(
        db=session, interval_type=SQLGene, build=build
    )
    LOG.info(f"{nr_loaded_genes} genes loaded into the database.")
    return nr_loaded_genes, "OK"
