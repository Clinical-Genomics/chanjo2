from typing import List, Union

from chanjo2.models import pydantic_models, sql_models
from sqlalchemy.orm import Session


### Case utils
def get_cases(db: Session, skip: int = 0, limit: int = 100) -> List[pydantic_models.CaseRead]:
    """Return all cases"""
    return db.query(sql_models.Case).offset(skip).limit(limit).all()


def get_case(db: Session, case_name: str) -> pydantic_models.CaseRead:
    """Return a specific case by providing its ID"""
    return db.query(sql_models.Case).filter(sql_models.Case.name == case_name).first()


def create_case(db: Session, case: pydantic_models.CaseCreate) -> pydantic_models.CaseRead:
    """Create a case"""
    db_sample = sql_models.Case(name=case.name, display_name=case.display_name)
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample


### Sample utils
def get_samples(db: Session, skip: int = 0, limit: int = 100) -> List[pydantic_models.SampleRead]:
    """Return all samples"""
    return db.query(sql_models.Sample).offset(skip).limit(limit).all()


def get_case_samples(db: Session, case_name: str) -> List[pydantic_models.SampleRead]:
    """Return all samples for a given case ID"""
    return (
        db.query(sql_models.Sample)
        .join(sql_models.Case)
        .filter(sql_models.Case.name == case_name)
        .all()
    )


def get_sample(db: Session, sample_name: int) -> pydantic_models.SampleRead:
    """Return a specific sample by its ID"""
    return db.query(sql_models.Sample).filter(sql_models.Sample.name == sample_name).first()


def create_case_sample(
    db: Session, sample: pydantic_models.SampleCreate
) -> Union[pydantic_models.SampleRead, None]:
    """Create a sample"""
    # Check if sample's case exists first
    case_obj = db.query(sql_models.Case).filter(sql_models.Case.name == sample.case_name).first()
    if not case_obj:
        return

    # Insert new sample
    db_sample = sql_models.Sample(
        name=sample.name,
        display_name=sample.display_name,
        case_id=case_obj.id,
        coverage_file_path=sample.coverage_file_path,
    )
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample
