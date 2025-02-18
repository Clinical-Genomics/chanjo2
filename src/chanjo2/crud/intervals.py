import logging
from typing import Dict, List, Optional, Union

from sqlalchemy import delete, func, or_, text
from sqlalchemy.orm import Session, query
from sqlalchemy.sql.expression import Delete

from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import Builds, TranscriptBase, TranscriptTag

LOG = logging.getLogger(__name__)


def delete_intervals_for_build(
    db: Session, interval_type: Union[SQLGene, SQLTranscript, SQLExon], build: Builds
) -> None:
    """Delete intervals from a given table by specifying a genome build."""
    statement: Delete = delete(interval_type).where(interval_type.build == build)
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


def bulk_insert_genes(db: Session, genes: List[SQLGene]):
    """Bulk insert genes into the database."""
    db.bulk_save_objects(genes)
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
        ensembl_ids_placeholder = ", ".join(f"'{e}'" for e in ensembl_ids)
        genes = genes.filter(
            text(
                f"""
                EXISTS (
                    SELECT 1
                    FROM json_each(genes.ensembl_ids)
                    WHERE value IN ({ensembl_ids_placeholder})
                )
                """
            )
        )
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


def bulk_insert_transcripts(db: Session, transcripts: List[TranscriptBase]):
    """Bulk insert transcripts into the database."""
    db.bulk_save_objects(transcripts)
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
            ensembl_gene_ids=[
                ensembl_id for gene in genes for ensembl_id in gene.ensembl_ids
            ],
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

    intervals = db.query(interval_type).filter(interval_type.build == build)

    def get_ensembl_gene_ids_from_gene_filter(
        filter_value: List[Union[str, int]], filter_column: str
    ) -> List[str]:
        """Helper function to get ensembl_gene_ids from either hgnc_ids or hgnc_symbols."""
        genes = (
            db.query(SQLGene.ensembl_ids).filter(filter_column.in_(filter_value)).all()
        )
        return [ensembl_id for gene in genes for ensembl_id in gene.ensembl_ids]

    if ensembl_ids:
        intervals: query.Query = intervals.filter(
            interval_type.ensembl_id.in_(ensembl_ids)
        )
    elif hgnc_ids:
        ensembl_gene_ids = get_ensembl_gene_ids_from_gene_filter(
            hgnc_ids, SQLGene.hgnc_id
        )
    elif hgnc_symbols:
        ensembl_gene_ids = get_ensembl_gene_ids_from_gene_filter(
            hgnc_symbols, SQLGene.hgnc_symbol
        )
    if ensembl_gene_ids:
        intervals = intervals.filter(
            interval_type.ensembl_gene_id.in_(ensembl_gene_ids)
        )

    if interval_type == SQLTranscript and transcript_tags:
        intervals = _filter_transcripts_by_tag(
            transcripts=intervals, transcript_tags=transcript_tags
        )

    if limit:
        return intervals.limit(limit).all()

    return intervals.all()


def bulk_insert_exons(db: Session, exons: List[SQLExon]) -> None:
    """Bulk insert exons into the database."""
    db.bulk_save_objects(exons)
    db.commit()


def get_interval_counts(db: Session) -> Dict:
    counts = {}
    for build in Builds.get_enum_values():
        counts[build] = {
            "number_of_genes": db.query(func.count(SQLGene.id))
            .filter(SQLGene.build == build)
            .scalar(),
            "number_of_transcripts": db.query(func.count(SQLTranscript.id))
            .filter(SQLTranscript.build == build)
            .scalar(),
            "number_of_exons": db.query(func.count(SQLExon.id))
            .filter(SQLExon.build == build)
            .scalar(),
        }
    return counts
