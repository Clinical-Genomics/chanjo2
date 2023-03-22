import logging
from typing import List, Tuple

from chanjo2.constants import GENES_FILE_HEADER
from chanjo2.crud.intervals import create_db_interval
from chanjo2.crud.tags import create_db_tag, create_tag_link
from chanjo2.models.pydantic_models import Builds, IntervalBase, TagBase, TagType
from chanjo2.models.sql_models import Interval as SQLInterval
from chanjo2.models.sql_models import Tag as SQLTag
from schug.load.biomart import EnsemblBiomartClient
from schug.load.ensembl import fetch_ensembl_genes
from schug.load.fetch_resource import stream_resource
from sqlmodel import Session

LOG = logging.getLogger("uvicorn.access")


async def resource_lines(url) -> Tuple[List[List], List]:
    """Returns header and lines of a downloaded resources as strings."""
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

    url: str = _ensembl_genes_url(build)
    header, lines = await resource_lines(url)
    if header != GENES_FILE_HEADER:
        LOG.warning(
            f"Ensembl genes file has an unexpected format:{header}. Expected format: {GENES_FILE_HEADER}"
        )
        return 0

    for line in lines[:10]:
        items = line.split("\t")

        # Load gene interval into the database
        interval: IntervalBase = IntervalBase(
            chromosome=items[0], start=items[1], stop=items[2]
        )
        db_interval: SQLInterval = create_db_interval(db=session, interval=interval)

        for col in [3, 4, 5]:
            # Create Ensembl ID, HGNC symbol, HGNC ID(s) tags
            tag: TagBase = TagBase(name=items[col], type=TagType.GENE, build=build)
            db_tag: SQLTag = create_db_tag(db=session, tag=tag)

            # Link the tag above to the genomic interval
            create_tag_link(db=session, interval_id=db_interval.id, tag_id=db_tag.id)

    return 0
