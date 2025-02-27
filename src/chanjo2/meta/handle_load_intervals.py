import logging
from typing import Iterator, List, Optional, Union

from sqlalchemy.orm import Session

from chanjo2.constants import (
    EXONS_FILE_HEADER,
    GENES_FILE_HEADER,
    TRANSCRIPTS_FILE_HEADER,
)
from chanjo2.crud.intervals import (
    bulk_insert_exons,
    bulk_insert_genes,
    bulk_insert_transcripts,
    count_intervals_for_build,
    delete_intervals_for_build,
)
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    Builds,
    ExonBase,
    IntervalType,
    TranscriptBase,
)

LOG = logging.getLogger(__name__)
MAX_NR_OF_RECORDS = 10_000
END_OF_PARSED_FILE: str = "[success]"


def _replace_empty_cols(line: str, nr_expected_columns: int) -> List[Union[str, None]]:
    """Split line into columns, replacing empty columns with None values."""
    cols = [
        None if cell == "" else cell.replace("HGNC:", "") for cell in line.split("\t")
    ]

    # Make sure that expected nr of cols are returned if last cols are blank
    cols += [None] * (nr_expected_columns - len(cols))
    return cols


async def update_genes(
    build: Builds, session: Session, lines: Optional[Iterator] = None
) -> Optional[int]:
    """Loads genes into the database."""

    LOG.warning(f"Updating genes. Genome build --> {build}")
    if lines is None:
        lines: Iterator[str] = read_resource_lines(
            build=build, interval_type=IntervalType.GENES
        )

    header = next(lines).split("\t")
    expected_header = GENES_FILE_HEADER[build]
    if header[: len(expected_header)] == expected_header is False:
        raise ValueError(
            f"Ensembl genes file has an unexpected format:{header}. Expected format: {GENES_FILE_HEADER[build]}"
        )

    LOG.warning(f"Deleting genes, transcripts, exons in build {build}")
    for interval_type in [SQLExon, SQLTranscript, SQLGene]:
        delete_intervals_for_build(db=session, interval_type=interval_type, build=build)

    genes_bulk: List[SQLGene] = []

    for line in lines:
        if line == END_OF_PARSED_FILE:
            break

        items: List = _replace_empty_cols(line=line, nr_expected_columns=len(header))
        if items == header:
            continue
        try:
            sql_gene = SQLGene(
                build=build,
                chromosome=items[0],
                start=int(items[1]),
                stop=int(items[2]),
                ensembl_ids=[items[3]],
                hgnc_symbol=items[4],
                hgnc_id=items[5],
            )

            session.add(sql_gene)

            if len(genes_bulk) > MAX_NR_OF_RECORDS:
                bulk_insert_genes(db=session, genes=genes_bulk)
                genes_bulk = []

        except Exception as ex:
            LOG.error(ex)
            return

    bulk_insert_genes(db=session, genes=genes_bulk)  # Load the remaining genes

    nr_loaded_genes: int = count_intervals_for_build(
        db=session, interval_type=SQLGene, build=build
    )
    LOG.info(f"{nr_loaded_genes} genes loaded into the database.")
    return nr_loaded_genes


async def update_transcripts(
    build: Builds, session: Session, lines: Optional[Iterator] = None
) -> Optional[int]:
    """Loads transcripts into the database."""

    LOG.warning(f"Updating transcripts. Genome build --> {build}")

    if lines is None:
        lines: Iterator[str] = read_resource_lines(
            build=build, interval_type=IntervalType.TRANSCRIPTS
        )

    header = next(lines).split("\t")
    expected_header = TRANSCRIPTS_FILE_HEADER[build]
    if header[: len(expected_header)] == expected_header is False:
        raise ValueError(
            f"Ensembl transcripts file has an unexpected format:{header}. Expected format: {TRANSCRIPTS_FILE_HEADER[build]}"
        )

    LOG.warning(f"Deleting transcripts in build {build}")
    delete_intervals_for_build(db=session, interval_type=SQLTranscript, build=build)

    transcripts_bulk: List[TranscriptBase] = []

    for line in lines:
        if line == END_OF_PARSED_FILE:
            break

        items: List = _replace_empty_cols(line=line, nr_expected_columns=len(header))
        if items == header:
            continue
        try:
            transcript = SQLTranscript(
                chromosome=items[0],
                ensembl_gene_id=items[1],
                ensembl_id=items[2],
                start=int(items[3]),
                stop=int(items[4]),
                refseq_mrna=items[5],
                refseq_mrna_pred=items[6],
                refseq_ncrna=items[7],
                refseq_mane_select=items[8] if build == Builds.build_38 else None,
                refseq_mane_plus_clinical=(
                    items[9] if build == Builds.build_38 else None
                ),
                build=build,
            )
            transcripts_bulk.append(transcript)

            if len(transcripts_bulk) > MAX_NR_OF_RECORDS:
                bulk_insert_transcripts(db=session, transcripts=transcripts_bulk)
                transcripts_bulk = []

        except Exception as ex:
            LOG.error(ex)
            return

    bulk_insert_transcripts(
        db=session, transcripts=transcripts_bulk
    )  # Load the remaining transcripts

    nr_loaded_transcripts: int = count_intervals_for_build(
        db=session, interval_type=SQLTranscript, build=build
    )
    LOG.info(f"{nr_loaded_transcripts} transcripts loaded into the database.")
    return nr_loaded_transcripts


async def update_exons(
    build: Builds, session: Session, lines: Optional[Iterator] = None
) -> Optional[int]:
    """Loads exons into the database."""

    LOG.warning(f"Updating exons. Genome build --> {build}")

    if lines is None:
        lines: Iterator[str] = read_resource_lines(
            build=build, interval_type=IntervalType.EXONS
        )

    header = next(lines).split("\t")
    expected_header = EXONS_FILE_HEADER[build]
    if header[: len(expected_header)] == expected_header is False:
        raise ValueError(
            f"Ensembl exons file has an unexpected format:{header}. Expected format: {EXONS_FILE_HEADER[build]}"
        )

    LOG.warning(f"Deleting exons in build {build}")
    delete_intervals_for_build(db=session, interval_type=SQLExon, build=build)

    exons_bulk: List[ExonBase] = []

    for line in lines:
        if line == END_OF_PARSED_FILE:
            break

        items: List = _replace_empty_cols(line=line, nr_expected_columns=len(header))
        if items == header:
            continue
        try:
            # Load Exon interval into the database
            exon = SQLExon(
                chromosome=items[0],
                ensembl_gene_id=items[1],
                ensembl_transcript_id=items[2],
                ensembl_id=items[3],
                start=int(items[4]),
                stop=int(items[5]),
                rank_in_transcript=int(items[-1]),
                build=build,
            )

            exons_bulk.append(exon)

            if len(exons_bulk) > MAX_NR_OF_RECORDS:
                bulk_insert_exons(db=session, exons=exons_bulk)
                exons_bulk = []

        except Exception as ex:
            LOG.error(ex)
            return

    bulk_insert_exons(db=session, exons=exons_bulk)  # Load the remaining exons

    nr_loaded_exons: int = count_intervals_for_build(
        db=session, interval_type=SQLExon, build=build
    )
    LOG.info(f"{nr_loaded_exons} exons loaded into the database.")

    return nr_loaded_exons
