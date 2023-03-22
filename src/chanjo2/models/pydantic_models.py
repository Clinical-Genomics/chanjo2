from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

import validators
from chanjo2.constants import WRONG_BED_FILE_MSG, WRONG_COVERAGE_FILE_MSG
from pydantic import BaseModel, validator


class Builds(str, Enum):
    build_37 = "GRCh37"
    build_38 = "GRCh38"


class CaseBase(BaseModel):
    name: str
    display_name: Optional[str] = None


class CaseCreate(CaseBase):
    pass


class SampleBase(BaseModel):
    name: str
    display_name: str
    coverage_file_path: str

    @validator("coverage_file_path", pre=True)
    def validate_coverage_path(cls, value: str) -> Any:
        if not Path(value).is_file() and not validators.url(value):
            raise ValueError(WRONG_COVERAGE_FILE_MSG)

        return value


class SampleCreate(SampleBase):
    case_name: str


class Sample(SampleBase):
    id: int
    created_at: datetime
    case_id: int

    class Config:
        orm_mode = True


class Case(CaseBase):
    id: int
    samples: List[Sample] = []

    class Config:
        orm_mode = True


class TagBase(BaseModel):
    name: str
    build: Builds


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: int


class IntervalBase(BaseModel):
    name: str
    chromosome: str
    start: int
    stop: int


class IntervalCreate(IntervalBase):
    pass


class IntervalRead(IntervalBase):
    id: int
    tags: List[TagRead] = []


class CoverageInterval(BaseModel):
    chromosome: str
    start: Optional[int]
    end: Optional[int]
    individual_id: Optional[int]
    interval_id: Optional[int]
    case_id: Optional[int]
    mean_coverage: float
