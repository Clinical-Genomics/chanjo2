import logging
from typing import List, Optional, Union

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session, query
from sqlalchemy.sql.expression import Delete

from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    Builds,
    ExonBase,
    GeneBase,
    TranscriptBase,
    TranscriptTag,
)

LOG = logging.getLogger(__name__)


def delete_intervals_for_build(
    db: Session, interval_type: Union[SQLGene, SQLTranscript, SQLExon], build: Builds
) -> None:
    """Delete intervals from a given table by specifying a genome build."""
    statement: Delete = delete(interval_type).where(interval_type.build == build)
    LOG.info(f"Executing statement: {statement}")
    db.execute(statement)


def count_intervals_for_build(
    db: Session, interval_type: Union[SQLGene, SQLTranscript, SQLExon], build: Builds
) -> int:
    """Count intervals in table by specifying a genome build."""
    return db.query(interval_type).where(interval_type.build == build).count()


def _filter_intervals_by_build(
    intervals: query.Query,
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    build: Builds,
) -> query.Query:
    """Filter intervals by genome build."""
    return intervals.filter(interval_type.build == build)


def create_db_gene(gene: GeneBase) -> SQLGene:
    """Create and return a SQL gene object."""
    return SQLGene(
        build=gene.build.value,
        chromosome=gene.chromosome,
        start=gene.start,
        stop=gene.stop,
        ensembl_id=gene.ensembl_id,
        hgnc_symbol=gene.hgnc_symbol,
        hgnc_id=gene.hgnc_id,
    )


def bulk_insert_genes(db: Session, genes: List[GeneBase]):
    """Bulk insert genes into the database."""
    db.bulk_save_objects([create_db_gene(gene) for gene in genes])
    db.commit()


def get_genes(
    db: Session,
    build: Builds,
    ensembl_ids: Optional[List[str]],
    hgnc_ids: Optional[List[int]],
    hgnc_symbols: Optional[List[str]],
    limit: Optional[int],
) -> List[SQLGene]:
    """Return genes according to specified fields."""
    genes: query.Query = db.query(SQLGene)

    if ensembl_ids:
        genes: query.Query = genes.filter(SQLGene.ensembl_id.in_(ensembl_ids))
    elif hgnc_ids:
        genes: query.Query = genes.filter(SQLGene.hgnc_id.in_(hgnc_ids))
    elif hgnc_symbols:
        genes: query.Query = genes.filter(SQLGene.hgnc_symbol.in_(hgnc_symbols))

    genes: query.Query = _filter_intervals_by_build(
        intervals=genes, interval_type=SQLGene, build=build
    )
    if limit:
        return genes.limit(limit).all()
    return genes.all()


def create_db_transcript(transcript: TranscriptBase) -> SQLTranscript:
    """Create and return a SQL transcript object."""

    return SQLTranscript(
        chromosome=transcript.chromosome,
        start=transcript.start,
        stop=transcript.stop,
        ensembl_id=transcript.ensembl_id,
        ensembl_gene_id=transcript.ensembl_gene_id,
        refseq_mrna=transcript.refseq_mrna,
        refseq_mrna_pred=transcript.refseq_mrna_pred,
        refseq_ncrna=transcript.refseq_ncrna,
        refseq_mane_select=transcript.refseq_mane_select,
        refseq_mane_plus_clinical=transcript.refseq_mane_plus_clinical,
        build=transcript.build,
    )


def bulk_insert_transcripts(db: Session, transcripts: List[TranscriptBase]):
    """Bulk insert transcripts into the database."""
    db.bulk_save_objects(
        [create_db_transcript(transcript=transcript) for transcript in transcripts]
    )
    db.commit()


def get_hgnc_gene(db: Session, build: Builds, hgnc_id: int) -> SQLGene:
    """Return a gene object by its HGNC ID."""
    gene_query: query.Query = (
        db.query(SQLGene)
        .filter(SQLGene.hgnc_id == hgnc_id)
        .filter(SQLGene.build == build)
    )
    return gene_query.first()


def _filter_transcripts_by_tag(
    transcripts: query.Query, transcript_tags: List[TranscriptTag] = []
) -> query.Query:
    """Return transcripts which contain one or more RefSeq tag."""

    not_null_filters = []
    for tag in transcript_tags:
        not_null_filters.append(getattr(SQLTranscript, tag).isnot(None))
    return transcripts.filter(or_(*not_null_filters))


def set_sql_intervals(
    db: Session,
    interval_type: Union[SQLExon, SQLGene, SQLTranscript],
    genes: List[SQLGene],
    transcript_tags=Optional[List[TranscriptTag]],
) -> List[Union[SQLGene, SQLTranscript, SQLExon]]:
    """If SQL intervals are genes return them as they are, otherwise return genes, transcripts or exons."""
    if interval_type == SQLGene:
        sql_intervals: List[SQLGene] = genes
    else:
        sql_intervals: List[Union[SQLTranscript, SQLExon]] = get_gene_intervals(
            db=db,
            build=genes[0].build,
            interval_type=interval_type,
            ensembl_ids=None,
            hgnc_ids=None,
            hgnc_symbols=None,
            ensembl_gene_ids=[gene.ensembl_id for gene in genes],
            limit=None,
            transcript_tags=transcript_tags,
        )
    return sql_intervals


def get_gene_intervals(
    db: Session,
    build: Builds,
    interval_type: Union[SQLTranscript, SQLExon],
    ensembl_ids: Optional[List[str]] = [],
    hgnc_ids: Optional[List[int]] = [],
    hgnc_symbols: Optional[List[str]] = [],
    ensembl_gene_ids: Optional[List[str]] = [],
    limit: Optional[int] = None,
    transcript_tags: Optional[List[TranscriptTag]] = [],
) -> List[Union[SQLTranscript, SQLExon]]:
    """Retrieve transcripts or exons from a list of genes."""

    intervals: query.Query = db.query(interval_type).join(SQLGene)
    if ensembl_ids:
        intervals: query.Query = intervals.filter(
            interval_type.ensembl_id.in_(ensembl_ids)
        )
    elif ensembl_gene_ids:
        intervals: query.Query = intervals.filter(
            interval_type.ensembl_gene_id.in_(ensembl_gene_ids)
        )
    elif hgnc_ids:
        intervals: query.Query = intervals.filter(SQLGene.hgnc_id.in_(hgnc_ids))
    elif hgnc_symbols:
        intervals: query.Query = intervals.filter(SQLGene.hgnc_symbol.in_(hgnc_symbols))

    if interval_type == SQLTranscript and transcript_tags:
        intervals = _filter_transcripts_by_tag(
            transcripts=intervals, transcript_tags=transcript_tags
        )

    intervals: query.Query = intervals.filter(interval_type.build == build)

    if limit:
        return intervals.limit(limit).all()

    return intervals.all()


def create_db_exon(exon: ExonBase) -> SQLExon:
    """Create and return a SQL exon object."""

    return SQLExon(
        chromosome=exon.chromosome,
        start=exon.start,
        stop=exon.stop,
        rank_in_transcript=exon.rank_in_transcript,
        ensembl_id=exon.ensembl_id,
        ensembl_gene_id=exon.ensembl_gene_id,
        ensembl_transcript_id=exon.ensembl_transcript_id,
        build=exon.build,
    )


def bulk_insert_exons(db: Session, exons: List[ExonBase]) -> None:
    """Bulk insert exons into the database."""
    db.bulk_save_objects([create_db_exon(exon=exon) for exon in exons])
    db.commit()
