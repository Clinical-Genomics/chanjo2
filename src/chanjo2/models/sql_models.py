from dataclasses import dataclass

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from chanjo2.dbutil import Base
from chanjo2.models.pydantic_models import Builds

CaseSample = Table(
    "case_sample",
    Base.metadata,
    Column("case_id", Integer, ForeignKey("cases.id"), primary_key=True),
    Column("sample_id", Integer, ForeignKey("samples.id"), primary_key=True),
)


@dataclass
class Case(Base):
    """Used to define a case containing samples."""

    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(64), nullable=True, unique=False)
    samples = relationship("Sample", secondary=CaseSample, back_populates="cases")


@dataclass
class Sample(Base):
    """Used to define a single sample belonging to a Case."""

    __tablename__ = "samples"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(64), nullable=True, unique=False)
    track_name = Column(String(64), nullable=True, unique=False)
    coverage_file_path = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cases = relationship("Case", secondary=CaseSample, back_populates="samples")


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
    ensembl_id = Column(String(24), nullable=False)
    hgnc_id = Column(Integer, nullable=True)
    hgnc_symbol = Column(String(64), nullable=True)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )
    __table_args__ = (
        Index("gene_idx_ensembl_id_build", "ensembl_id", "build"),
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
    ensembl_gene_id = Column(String(24), ForeignKey("genes.ensembl_id"), nullable=False)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )

    genes = relationship(
        "Gene",
        primaryjoin="Transcript.ensembl_gene_id==Gene.ensembl_id",
    )

    __table_args__ = (
        Index("transcript_idx_ensembl_gene_build", "ensembl_gene_id", "build"),
    )


@dataclass
class Exon(Base):
    """Used to define an exon entity."""

    __tablename__ = "exons"
    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)
    ensembl_id = Column(String(24), nullable=False, index=False)
    ensembl_gene_id = Column(String(24), ForeignKey("genes.ensembl_id"), nullable=False)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )

    genes = relationship(
        "Gene",
        primaryjoin="Exon.ensembl_gene_id==Gene.ensembl_id",
    )

    __table_args__ = (
        Index("exon_idx_ensembl_gene:_build", "ensembl_gene_id", "build"),
    )
