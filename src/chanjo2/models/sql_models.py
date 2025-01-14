from dataclasses import dataclass

from sqlalchemy import JSON, Column, Enum, ForeignKey, Index, Integer, String

from chanjo2.dbutil import Base
from chanjo2.models.pydantic_models import Builds


@dataclass
class Interval(Base):
    """Used to define a single genomic interval."""

    __tablename__ = "intervals"

    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)


@dataclass
class Gene(Base):
    """Used to define a gene entity."""

    __tablename__ = "genes"
    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)
    ensembl_ids = Column(JSON, nullable=False)
    hgnc_id = Column(Integer, nullable=True, index=True)
    hgnc_symbol = Column(String(64), nullable=True)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )
    __table_args__ = (
        Index("gene_idx_hgnc_id_build", "hgnc_id", "build"),
        Index("gene_idx_hgnc_symbol_build", "hgnc_symbol", "build"),
    )


@dataclass
class Transcript(Base):
    """Used to define a transcript entity."""

    __tablename__ = "transcripts"
    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)
    ensembl_id = Column(String(24), nullable=False, index=True)
    refseq_mrna = Column(String(24), nullable=True)
    refseq_mrna_pred = Column(String(24), nullable=True)
    refseq_ncrna = Column(String(24), nullable=True)
    refseq_mane_select = Column(String(24), nullable=True, index=True)
    refseq_mane_plus_clinical = Column(String(24), nullable=True, index=True)
    ensembl_gene_id = Column(String(24), nullable=False, index=True)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )

    __table_args__ = (
        Index("ensembl_gene_build_id", "ensembl_gene_id", "build", "ensembl_id"),
    )


@dataclass
class Exon(Base):
    """Used to define an exon entity."""

    __tablename__ = "exons"
    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)
    rank_in_transcript = Column(Integer, nullable=False)
    ensembl_id = Column(String(24), nullable=False)
    ensembl_transcript_id = Column(String(24), nullable=False, index=True)
    ensembl_gene_id = Column(String(24), nullable=False, index=True)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )

    __table_args__ = (
        Index(
            "exon_idx_ensembl_gene_build_transcript",
            "ensembl_gene_id",
            "build",
            "ensembl_transcript_id",
        ),
    )
