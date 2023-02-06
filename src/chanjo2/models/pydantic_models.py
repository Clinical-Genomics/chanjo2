from datetime import datetime
from enum import Enum
from typing import List, Union

from pydantic import BaseModel


class Builds(str, Enum):
    build_37 = "GRCh37"
    build_38 = "GRCh38"


class CaseBase(BaseModel):
    name: str
    display_name: Union[str, None] = None


class CaseCreate(CaseBase):
    pass


class SampleBase(BaseModel):
    name: str
    display_name: str
    coverage_file_path: str


class SampleCreate(SampleBase):
    case_name: str


class SampleRead(SampleBase):
    id: int
    created_at: datetime
    case_id: int

    class Config:
        orm_mode = True


class Case(CaseBase):
    id: int
    samples: List[SampleRead] = []

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
    start: int
    end: int
    individual_id: int
    interval_id: int
    case_id: int
    mean_coverage: float
