from datetime import datetime
from typing import Enum, List, Union

from pydantic import BaseModel


class Builds(str, Enum):
    build_37 = "GRCh37"
    build_38 = "GRCh38"


class CaseBase(BaseModel):
    name: str
    display_name: Union[str, None] = None


class CaseCreate(CaseBase):
    pass


class CaseRead(CaseBase):
    id: int
    samples = List[SampleRead] = []


class SampleBase(BaseModel):
    name: str
    display_name: str
    coverage_file_path: str


class SampleCreate(SampleBase):
    created_at: datetime


class SampleRead(SampleBase):
    id: int
    case_id: int
    created_at: datetime
    case_id: int
    case: CaseRead


class TagBase(BaseModel):
    name: str
    build: Builds


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: int
    intervals = List[IntervalRead] = []


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


"""
class CoverageInterval(BaseModel):
    chromosome: str
    start: int
    end: int
    individual_id: str
    interval_id: str
    mean_coverage: float
"""
