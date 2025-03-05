import logging
from typing import Iterator, List, Optional, Union

from sqlalchemy.orm import Session
from tqdm import tqdm

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
from chanjo2.meta.handle_bed import resource_lines
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


def update_interval_table(
    interval_type: IntervalType,
    build: Builds,
    file_path: Optional[str],
    session: Session,
) -> None:
    """This function is runned in background and is responsible for updating a specific interval table of the database."""

    nlines: int = sum(1 for _ in open(file_path))
    interval_lines: Iterator[str] = resource_lines(file_path=file_path)

    if interval_type == IntervalType.GENES:
        update_genes(build=build, lines=interval_lines, nlines=nlines, session=session)
    elif interval_type == IntervalType.TRANSCRIPTS:
        update_transcripts(
            build=build, lines=interval_lines, nlines=nlines, session=session
        )
    elif interval_type == IntervalType.EXONS:
        update_exons(build=build, lines=interval_lines, nlines=nlines, session=session)


def _replace_empty_cols(line: str, nr_expected_columns: int) -> List[Union[str, None]]:
    """Split line into columns, replacing empty columns with None values."""
    cols = [
        None if cell == "" else cell.replace("HGNC:", "") for cell in line.split("\t")
    ]

    # Make sure that expected nr of cols are returned if last cols are blank
    cols += [None] * (nr_expected_columns - len(cols))
    return cols


def update_genes(build: Builds, session: Session, lines: Iterator, nlines: int) -> None:
    """Loads genes into the database, replacing existing ones."""

    LOG.warning(f"Updating genes. Genome build --> {build.value}")

    header = next(lines).split("\t")
    expected_header = GENES_FILE_HEADER[build]
    if header[: len(expected_header)] == expected_header is False:
        raise ValueError(
            f"Ensembl genes file has an unexpected format:{header}. Expected format: {GENES_FILE_HEADER[build]}"
        )

    LOG.warning(f"Deleting genes, transcripts, exons in build {build.value}")
    delete_intervals_for_build(db=session, interval_type=SQLGene, build=build)

    genes_bulk: List[SQLGene] = []

    with tqdm(total=nlines - 1, desc="Processing gene lines", unit="line") as pbar:
        for line in lines:
            line = line.strip()
            if END_OF_PARSED_FILE in line:
                break
            items: List = _replace_empty_cols(
                line=line, nr_expected_columns=len(header)
            )
            if items == header:
                continue
            sql_gene = SQLGene(
                build=build,
                chromosome=items[0],
                start=int(items[1]),
                stop=int(items[2]),
                ensembl_ids=[items[3]],
                hgnc_symbol=items[4],
                hgnc_id=items[5],
            )

            genes_bulk.append(sql_gene)

            # Bulk insert when threshold is reached
            if len(genes_bulk) >= MAX_NR_OF_RECORDS:
                bulk_insert_genes(db=session, genes=genes_bulk)
                genes_bulk = []

            pbar.update(1)

    # Insert remaining genes
    if genes_bulk:
        bulk_insert_genes(db=session, genes=genes_bulk)

    pbar.close()

    nr_loaded_genes: int = count_intervals_for_build(
        db=session, interval_type=SQLGene, build=build
    )
    LOG.warning(f"{nr_loaded_genes} genes loaded into the database.")


def update_transcripts(
    build: Builds, session: Session, lines: [Iterator], nlines: int
) -> None:
    """Loads transcripts into the database."""

    LOG.warning(f"Updating transcripts. Genome build --> {build.value}")

    header = next(lines).split("\t")
    expected_header = TRANSCRIPTS_FILE_HEADER[build]
    if header[: len(expected_header)] == expected_header is False:
        raise ValueError(
            f"Ensembl transcripts file has an unexpected format:{header}. Expected format: {TRANSCRIPTS_FILE_HEADER[build]}"
        )

    LOG.warning(f"Deleting transcripts in build {build.value}")
    delete_intervals_for_build(db=session, interval_type=SQLTranscript, build=build)

    transcripts_bulk: List[TranscriptBase] = []

    with tqdm(
        total=nlines - 1, desc="Processing transcripts lines", unit="line"
    ) as pbar:
        for line in lines:
            line = line.strip()
            if END_OF_PARSED_FILE in line:
                break
            items: List = _replace_empty_cols(
                line=line, nr_expected_columns=len(header)
            )
            if items == header:
                continue
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

            # Bulk insert when threshold is reached
            if len(transcripts_bulk) > MAX_NR_OF_RECORDS:
                bulk_insert_transcripts(db=session, transcripts=transcripts_bulk)
                transcripts_bulk = []

            pbar.update(1)

    # Insert remaining genes
    if transcripts_bulk:
        bulk_insert_transcripts(db=session, transcripts=transcripts_bulk)

    pbar.close()
    nr_loaded_transcripts: int = count_intervals_for_build(
        db=session, interval_type=SQLTranscript, build=build
    )
    LOG.warning(f"{nr_loaded_transcripts} transcripts loaded into the database.")


def update_exons(
    build: Builds, session: Session, lines: [Iterator], nlines: int
) -> None:
    """Loads exons into the database."""

    LOG.warning(f"Updating exons. Genome build --> {build.value}")

    header = next(lines).split("\t")
    expected_header = EXONS_FILE_HEADER[build]
    if header[: len(expected_header)] == expected_header is False:
        raise ValueError(
            f"Ensembl exons file has an unexpected format:{header}. Expected format: {EXONS_FILE_HEADER[build]}"
        )

    LOG.warning(f"Deleting exons in build {build.value}")
    delete_intervals_for_build(db=session, interval_type=SQLExon, build=build)

    exons_bulk: List[ExonBase] = []

    with tqdm(total=nlines - 1, desc="Processing exons lines", unit="line") as pbar:
        for line in lines:
            line = line.strip()
            if END_OF_PARSED_FILE in line:
                break
            items: List = _replace_empty_cols(
                line=line, nr_expected_columns=len(header)
            )
            if items == header:
                continue
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

            # Bulk insert when threshold is reached
            if len(exons_bulk) > MAX_NR_OF_RECORDS:
                bulk_insert_exons(db=session, exons=exons_bulk)
                exons_bulk = []

            pbar.update(1)

    # Insert remaining genes
    if exons_bulk:
        bulk_insert_exons(db=session, exons=exons_bulk)

    pbar.close()
    nr_loaded_exons: int = count_intervals_for_build(
        db=session, interval_type=SQLExon, build=build
    )
    LOG.warning(f"{nr_loaded_exons} exons loaded into the database.")
