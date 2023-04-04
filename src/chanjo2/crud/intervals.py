import logging
from typing import List, Optional, Union

from chanjo2.models.pydantic_models import Builds, Gene, GeneBase, TranscriptBase
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript
from sqlalchemy import delete, insert, select
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session, query
from sqlalchemy.sql.expression import Delete, Select

LOG = logging.getLogger("uvicorn.access")


def delete_intervals_for_build(
    db: Session, interval_type: Union[SQLGene, SQLTranscript], build: Builds
) -> None:
    """Delete intervals from a given table by specifying a genome build."""
    statement: Delete = delete(interval_type).where(interval_type.build == build)
    LOG.warning(f"Executing statement: {statement}")
    db.execute(statement)


def count_intervals_for_build(
    db: Session, interval_type: Union[SQLGene, SQLTranscript], build: Builds
) -> int:
    """Count intervals in table by specifying a genome build."""
    return db.query(interval_type).where(interval_type.build == build).count()


def _filter_intervals_by_build(
    intervals: query.Query, interval_type: Union[SQLGene, SQLTranscript], build: Builds
) -> List[Union[SQLGene]]:
    """Filter samples by sample name."""
    return intervals.filter(interval_type.build == build)


def create_db_gene(gene: GeneBase) -> SQLGene:
    """Create a SQL gene object."""
    return SQLGene(
        build=gene.build,
        chromosome=gene.chromosome,
        start=gene.start,
        stop=gene.stop,
        ensembl_id=gene.ensembl_id,
        hgnc_symbol=gene.hgnc_symbol,
        hgnc_id=gene.hgnc_id,
    )


def bulk_insert_genes(db: Session, gene_list: List[Gene]):
    """Bulk insert genes into the database."""
    db.bulk_save_objects([create_db_gene(gene) for gene in gene_list])
    db.commit()


def get_genes(db: Session, build: Builds, limit: int) -> List[Gene]:
    """Returns genes in the given genome build."""
    return (
        _filter_intervals_by_build(
            intervals=db.query(SQLGene), interval_type=SQLGene, build=build
        )
        .limit(limit)
        .all()
    )


def create_db_transcript(db: Session, transcript: TranscriptBase) -> SQLTranscript:
    """Create a SQL transcript object."""

    ensembl_gene = (
        db.query(SQLGene)
        .filter(SQLGene.ensembl_id == transcript.ensembl_gene_id)
        .first()
    )

    return SQLTranscript(
        chromosome=transcript.chromosome,
        start=transcript.start,
        stop=transcript.stop,
        ensembl_id=transcript.ensembl_id,
        ensembl_gene_ref=ensembl_gene.id if ensembl_gene else None,
        ensembl_gene_id=transcript.ensembl_gene_id,
        refseq_mrna=transcript.refseq_mrna,
        refseq_mrna_pred=transcript.refseq_mrna_pred,
        refseq_ncrna=transcript.refseq_ncrna,
        refseq_mane_select=transcript.refseq_mane_select,
        refseq_mane_plus_clinical=transcript.refseq_mane_plus_clinical,
        build=transcript.build,
    )


def bulk_insert_transcripts(db: Session, transcript_list: List[Gene]):
    """Bulk insert transcripts into the database."""
    db.bulk_save_objects([create_db_transcript(db, tx) for tx in transcript_list])
    db.commit()


def get_transcripts(db: Session, build: Builds, limit: int) -> List[Gene]:
    """Returns genes in the given genome build."""
    return (
        _filter_intervals_by_build(
            intervals=db.query(SQLTranscript), interval_type=SQLTranscript, build=build
        )
        .limit(limit)
        .all()
    )
