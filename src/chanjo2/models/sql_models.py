from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from chanjo2.dbutil import Base
from chanjo2.models.pydantic_models import Builds


class Case(Base):
    """Used to define a group of samples."""

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(64), nullable=True, unique=False)

    samples = relationship("Sample", back_populates="case")


class Sample(Base):
    """Used to define a single sample belonging to a Case"""

    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    display_name = Column(String(64), nullable=True, unique=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    coverage_file_path = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("Case", back_populates="samples")


class Interval(Base):
    """Used to define a single genomic interval."""

    __tablename__ = "intervals"

    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)


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
        Index("geneidx_build_ensemble_id", "build", "ensembl_id"),
        Index(
            "geneidx_build_hgnc_id",
            "build",
            "hgnc_id",
        ),
        Index(
            "geneidx_build_hgnc_symbol",
            "build",
            "hgnc_symbol",
        ),
    )


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
    ensembl_gene_id = Column(String(24), nullable=False)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )
    __table_args__ = (Index("txidx_build_ensemble_gene", "build", "ensembl_gene_id"),)


class Exon(Base):
    """Used to define an exon entity."""

    __tablename__ = "exons"
    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)
    ensembl_id = Column(String(24), nullable=False, index=False)
    ensembl_gene_id = Column(String(24), nullable=False)
    build = Column(
        Enum(Builds, values_callable=lambda x: Builds.get_enum_values()), index=True
    )
    __table_args__ = (Index("exonidx_build_ensemble_gene", "build", "ensembl_gene_id"),)
