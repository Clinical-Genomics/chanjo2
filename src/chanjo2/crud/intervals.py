from typing import List, Optional

from chanjo2.models.pydantic_models import GeneBase
from chanjo2.models.sql_models import Gene as SQLGene
from sqlalchemy.orm import Session, query


def create_db_gene(db: Session, gene: GeneBase):
    """Load a gene into the database."""
    db_gene = SQLGene(
        build=gene.build,
        chromosome=gene.chromosome,
        start=gene.start,
        stop=gene.stop,
        ensembl_id=gene.ensembl_id,
        hgnc_symbol=gene.hgnc_symbol,
        hgnc_id=gene.hgnc_id,
    )
    db.add(db_gene)
    db.commit()
    db.refresh(db_gene)
    return db_gene


def count_genes(db: Session) -> int:
    """Count number of genes present in the database."""
    return db.query(SQLGene.id).count()
