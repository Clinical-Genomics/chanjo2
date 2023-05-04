from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Tuple

import validators
from pydantic import BaseModel, validator, Field

from chanjo2.constants import WRONG_COVERAGE_FILE_MSG


class Builds(str, Enum):
    build_37 = "GRCh37"
    build_38 = "GRCh38"

    @staticmethod
    def get_enum_values() -> List[str]:
        """Returns the values of the available genome builds."""
        return [member.value for member in Builds]


class IntervalType(str, Enum):
    GENES = "genes"
    TRANSCRIPTS = "transcripts"
    EXONS = "exons"
    CUSTOM = "custom_intervals"


class CaseBase(BaseModel):
    display_name: Optional[str] = None
    name: str


class CaseCreate(CaseBase):
    pass


class SampleBase(BaseModel):
    coverage_file_path: str
    display_name: str
    name: str

    @validator("coverage_file_path", pre=True)
    def validate_coverage_path(cls, value: str) -> Any:
        if not Path(value).is_file() and not validators.url(value):
            raise ValueError(WRONG_COVERAGE_FILE_MSG)

        return value


class SampleCreate(SampleBase):
    case_name: str


class Sample(SampleBase):
    case_id: int
    created_at: datetime
    id: int

    class Config:
        orm_mode = True


class Case(CaseBase):
    id: int
    samples: List[Sample] = []

    class Config:
        orm_mode = True


class IntervalBase(BaseModel):
    chromosome: str
    start: int
    stop: int


class Interval(IntervalBase):
    id: int


class GeneBase(IntervalBase):
    build: Builds
    ensembl_id: str
    hgnc_id: Optional[int]
    hgnc_symbol: Optional[str]


class GeneQuery(BaseModel):
    build: Builds
    ensembl_ids: Optional[List[str]]
    hgnc_ids: Optional[List[int]]
    hgnc_symbols: Optional[List[str]]
    limit: Optional[int] = 100


class GeneIntervalQuery(GeneQuery):
    ensembl_gene_ids: Optional[List[str]]


class Gene(IntervalBase):
    id: int


class TranscriptBase(IntervalBase):
    build: Builds
    ensembl_id: str
    ensembl_gene_id: str
    refseq_mrna: Optional[str]
    refseq_mrna_pred: Optional[str]
    refseq_ncrna: Optional[str]
    refseq_mane_select: Optional[str]
    refseq_mane_plus_clinical: Optional[str]


class Transcript(TranscriptBase):
    id: int


class ExonBase(IntervalBase):
    build: Builds
    ensembl_id: str
    ensembl_gene_id: str
    ensembl_transcript_id: str


class Exon(IntervalBase):
    id: int


class CoverageInterval(BaseModel):
    chromosome: str
    completeness: List[Tuple] = Field(default_factory=list)
    ensembl_gene_id: Optional[str]
    end: Optional[int]
    hgnc_id: Optional[int]
    hgnc_symbol: Optional[str]
    interval_id: Optional[int]
    mean_coverage: float
    start: Optional[int]


class SampleGeneQuery(BaseModel):
    build: Builds
    completeness_thresholds: Optional[List[int]]
    ensembl_ids: Optional[List[str]]
    hgnc_ids: Optional[List[int]]
    hgnc_symbols: Optional[List[str]]
    sample_name: str


class SampleGeneIntervalQuery(BaseModel):
    build: Builds
    ensembl_gene_ids: Optional[List[str]]
    hgnc_ids: Optional[List[int]]
    hgnc_symbols: Optional[List[str]]
    sample_name: str
