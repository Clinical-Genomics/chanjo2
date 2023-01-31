import logging

from chanjo2.models import pydantic_models, sql_models
from sqlalchemy.orm import Session

LOG = logging.getLogger("uvicorn.access")


### Case utils
def get_cases(db: Session, skip: int = 0, limit: int = 100):
    """Return all cases"""
    return db.query(sql_models.Case).offset(skip).limit(limit).all()


def get_case(db: Session, case_name: str):
    """Return a specific case by providing its ID"""
    return db.query(sql_models.Case).filter(sql_models.Case.name == case_name).first()


def create_case(db: Session, case: pydantic_models.CaseCreate):
    """Create a case"""
    db_sample = sql_models.Case(name=case.name, display_name=case.display_name)
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample


### Sample utils
def get_samples(db: Session, skip: int = 0, limit: int = 100):
    """Return all samples"""
    return db.query(sql_models.Sample).offset(skip).limit(limit).all()


def get_case_samples(db: Session, case_id: int):
    """Return all samples for a given case ID"""
    return db.query(sql_models.Sample).filter(sql_models.Sample.id == case_id)


def get_sample(db: Session, sample_id: int):
    """Return a specific sample by its ID"""
    return db.query(sql_models.Sample).filter(sql_models.Sample.id == sample_id).first()


def create_case_sample(db: Session, sample: pydantic_models.SampleCreate):
    """Create a sample"""
    # Check if sample's case exists first
    case_obj = (
        db.query(sql_models.Case)
        .filter(sql_models.Case.name == sample.case_name)
        .first()
    )
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

    # Return complete case with sample info
    return db.query(sql_models.Case).filter(sql_models.Case.id == case_obj.id)
