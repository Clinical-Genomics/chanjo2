from chanjo2.dbutil import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Case(Base):
    """Used to define a group of samples"""

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True)
    display_name = Column(String(64), nullable=True, unique=False)


class Sample(Base):
    """Used to define a single sample belonging to a Case"""

    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True)
    display_name = Column(String(64), nullable=True, unique=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    coverage_file_path = Column(String, nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())


class Tag(Base):
    """Used to define an attribute for one or more intervals, for instance GRCh38.
    It is in a relationship many-to-many with the Interval table"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, unique=True)


class Interval(Base):
    """Used to define a single genomic interval"""

    __tablename__ = "intervals"

    id = Column(Integer, primary_key=True, index=True)
    chromosome = Column(String(6), nullable=False, unique=True)
    start = Column(Integer, nullable=False)
    stop = Column(Integer, nullable=False)
    tags = Column(Integer, nullable=False)


class IntervalTag(Base):
    """Used to define the many-to-many relationship between the Interval and Tag tables"""

    __tablename__ = "interval_tag"

    interval_id = Column(Integer, ForeignKey("intervals.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("intervals.id"), primary_key=True)
