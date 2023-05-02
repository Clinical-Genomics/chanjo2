from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

import validators
from pydantic import BaseModel, validator

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


class IntervalFormat(str, Enum):
    ENSEMBL_IDS = "ensembl_ids"
    HGNC_IDS = "hgnc_ids"
    HGNC_SYMBOLS = "hgnc_symbols"
    ENSEMBL_GENE_IDS = "ensembl_gene_ids"


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


class IntervalBase(BaseModel):
    chromosome: str
    start: int
    stop: int


class Interval(IntervalBase):
    id: int


class GeneBase(IntervalBase):
    ensembl_id: str
    hgnc_id: Optional[int]
    hgnc_symbol: Optional[str]
    build: Builds


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
    ensembl_id: str
    ensembl_gene_id: str
    refseq_mrna: Optional[str]
    refseq_mrna_pred: Optional[str]
    refseq_ncrna: Optional[str]
    refseq_mane_select: Optional[str]
    refseq_mane_plus_clinical: Optional[str]
    build: Builds


class Transcript(TranscriptBase):
    id: int


class ExonBase(IntervalBase):
    ensembl_id: str
    ensembl_gene_id: str
    ensembl_transcript_id: str
    ensembl_id: str
    build: Builds


class Exon(IntervalBase):
    id: int


class CoverageInterval(BaseModel):
    ensembl_gene_id: Optional[str]
    hgnc_id: Optional[int]
    hgnc_symbol: Optional[str]
    chromosome: str
    start: Optional[int]
    end: Optional[int]
    interval_id: Optional[int]
    mean_coverage: float


class SampleGeneQuery(BaseModel):
    sample_name: str
    build: Builds
    ensembl_ids: Optional[List[str]]
    hgnc_ids: Optional[List[int]]
    hgnc_symbols: Optional[List[str]]
