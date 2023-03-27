from typing import List, Optional, Union

from chanjo2.models.pydantic_models import Builds, Gene, GeneBase
from chanjo2.models.sql_models import Gene as SQLGene
from sqlalchemy.orm import Session, query


def _filter_intervals_by_build(
    intervals: query.Query, interval_type: Union[SQLGene], build: Builds
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
    """Bulk insert genes into the database"""

    db.bulk_save_objects([create_db_gene(gene) for gene in gene_list])
    db.commit()


def count_genes(db: Session) -> int:
    """Count number of genes present in the database."""
    return db.query(SQLGene.id).count()


def get_genes(db: Session, build: Builds, limit: int) -> List[Gene]:
    """Returns genes in the given genome build"""
    query = db.query(SQLGene)
    return (
        _filter_intervals_by_build(intervals=query, interval_type=SQLGene, build=build)
        .limit(limit)
        .all()
    )
