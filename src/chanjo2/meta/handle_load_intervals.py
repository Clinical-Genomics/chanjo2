import logging
from typing import Iterator, List, Tuple, Union

import requests
from chanjo2.constants import (
    ENSEMBL_RESOURCE_CLIENT,
    GENES_FILE_HEADER,
    TRANSCRIPTS_FILE_HEADER,
)
from chanjo2.crud.intervals import (
    bulk_insert_genes,
    bulk_insert_transcripts,
    count_intervals_for_build,
    delete_intervals_for_build,
)
from chanjo2.models.pydantic_models import (
    Builds,
    GeneBase,
    IntervalType,
    TranscriptBase,
)
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript
from schug.load.biomart import EnsemblBiomartClient
from schug.load.fetch_resource import stream_resource
from schug.models.common import Build as SchugBuild
from sqlmodel import Session

LOG = logging.getLogger("uvicorn.access")


def resource_lines(url) -> Iterator[str]:
    """Returns lines of a remote resource file."""

    resp: requests.models.responses = requests.get(url, stream=True)
    return resp.iter_lines(decode_unicode=True)


def _get_ensembl_resource_url(build: Builds, interval_type: IntervalType) -> str:
    """Return the URL to download genes using the Ensembl Biomart."""
    shug_client: EnsemblBiomartClient = ENSEMBL_RESOURCE_CLIENT[interval_type](
        build=SchugBuild(build)
    )
    return shug_client.build_url(xml=shug_client.xml)


def _replace_empty_cols(line: str, nr_expected_columns: int) -> List[Union[str, None]]:
    """Split gene line into columns, replacing empty columns with None values."""
    cols = [None if col == "" else col.replace("HGNC:", "") for col in line.split("\t")]
    # Make sure that expected nr of cols are returned if last cols are blank
    cols += [None] * (nr_expected_columns - len(cols))
    return cols


async def update_genes(build: Builds, session: Session) -> int:
    """Loads genes into the database."""

    LOG.info(f"Loading gene intervals. Genome build --> {build}")
    url: str = _get_ensembl_resource_url(build=build, interval_type=IntervalType.GENES)

    lines: Iterator[str] = resource_lines(url=url)

    header = next(lines).split("\t")
    if header != GENES_FILE_HEADER[build]:
        raise ValueError(
            f"Ensembl genes file has an unexpected format:{header}. Expected format: {GENES_FILE_HEADER[build]}"
        )

    delete_intervals_for_build(db=session, interval_type=SQLGene, build=build)

    genes_bulk: List[SQLGene] = []

    for line in lines:
        items: List = _replace_empty_cols(line=line, nr_expected_columns=len(header))

        try:
            gene: GeneBase = GeneBase(
                build=build,
                chromosome=items[0],
                start=int(items[1]),
                stop=int(items[2]),
                ensembl_id=items[3],
                hgnc_symbol=items[4],
                hgnc_id=items[5],
            )
            genes_bulk.append(gene)

            if len(genes_bulk) > 10000:
                bulk_insert_genes(db=session, genes=genes_bulk)
                genes_bulk = []

        except Exception:
            LOG.info("End of resource file")

    bulk_insert_genes(db=session, genes=genes_bulk)

    nr_loaded_genes: int = count_intervals_for_build(
        db=session, interval_type=SQLGene, build=build
    )
    LOG.info(f"{nr_loaded_genes} genes loaded into the database.")
    return nr_loaded_genes


async def update_transcripts(build: Builds, session: Session) -> int:
    """Loads transcripts into the database."""

    LOG.info(f"Loading transcript intervals. Genome build --> {build}")
    url: str = _get_ensembl_resource_url(
        build=build, interval_type=IntervalType.TRANSCRIPTS
    )

    lines: Iterator[str] = resource_lines(url=url)

    header = next(lines).split("\t")
    if header != TRANSCRIPTS_FILE_HEADER[build]:
        raise ValueError(
            f"Ensembl transcripts file has an unexpected format:{header}. Expected format: {TRANSCRIPTS_FILE_HEADER[build]}"
        )

    delete_intervals_for_build(db=session, interval_type=SQLTranscript, build=build)

    transcripts_bulk: List[TranscriptBase] = []

    for line in lines:
        items: List = _replace_empty_cols(line=line, nr_expected_columns=len(header))

        try:
            transcript = TranscriptBase(
                chromosome=items[0],
                ensembl_gene_id=items[1],
                ensembl_id=items[2],
                start=int(items[3]),
                stop=int(items[4]),
                refseq_mrna=items[5],
                refseq_mrna_pred=items[6],
                refseq_ncrna=items[7],
                refseq_mane_select=items[8] if build == "GRCh38" else None,
                refseq_mane_plus_clinical=items[9] if build == "GRCh38" else None,
                build=build,
            )
            transcripts_bulk.append(transcript)

            if len(transcripts_bulk) > 10000:
                bulk_insert_transcripts(db=session, transcripts=transcripts_bulk)
                transcripts_bulk = []

        except Exception:
            LOG.info("End of resource file")

    bulk_insert_transcripts(
        db=session, transcripts=transcripts_bulk
    )  # Load the remaining transcripts

    nr_loaded_transcripts: int = count_intervals_for_build(
        db=session, interval_type=SQLTranscript, build=build
    )
    LOG.info(f"{nr_loaded_transcripts} transcripts loaded into the database.")
    return nr_loaded_transcripts
