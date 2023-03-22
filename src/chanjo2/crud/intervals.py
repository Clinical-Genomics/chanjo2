from typing import List, Optional

from chanjo2.models.pydantic_models import IntervalBase
from chanjo2.models.sql_models import Interval as SQLInterval
from sqlalchemy.orm import Session, query


def create_db_interval(db: Session, interval: IntervalBase) -> SQLInterval:
    """Create a case."""
    db_interval = SQLInterval(
        chromosome=interval.chromosome, start=interval.start, stop=interval.stop
    )
    db.add(db_interval)
    db.commit()
    db.refresh(db_interval)
    return db_interval


def count_intervals(db: Session) -> int:
    """Count number of intervals returned by a query"""
    return db.query(SQLInterval.id).count()
