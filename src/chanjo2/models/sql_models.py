from chanjo2.dbutil import Base
from chanjo2.models.pydantic_models import Builds
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


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
    coverage_file_path = Column(String, nullable=False)
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
    ensembl_id = Column(String(24), nullable=False, index=True)
    hgnc_id = Column(Integer, nullable=True, index=True)
    hgnc_symbol = Column(String(24), nullable=True, index=True)
    build = Column(Enum(Builds), index=True)
