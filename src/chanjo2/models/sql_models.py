from chanjo2.dbutil import Base
from chanjo2.models.pydantic_models import Builds, TagType
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


# Table used to define the many-to-many relationship between the Interval and Tag tables
interval_tag = Table(
    "interval_tag",
    Base.metadata,
    Column("interval_id", ForeignKey("intervals.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    """Used to define an attribute for one or more intervals.
    Can be a single gene, can be "Mane" or an entire Genome build.
    It is in a relationship many-to-many with the Interval table"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True, index=True)
    type = Column(Enum(TagType))
    build = Column(Enum(Builds))


class Interval(Base):
    """Used to define a single genomic interval"""

    __tablename__ = "intervals"

    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)
