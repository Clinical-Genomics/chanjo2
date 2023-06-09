from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Dict

import validators
from pydantic import BaseModel, validator, Field, root_validator

from chanjo2.constants import (
    WRONG_COVERAGE_FILE_MSG,
    MULTIPLE_GENE_LISTS_NOT_SUPPORTED_MSG,
    AMBIGUOUS_SAMPLES_INPUT,
)


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
    track_name: str
    name: str

    @validator("coverage_file_path", pre=True)
    def validate_coverage_path(cls, value: str) -> Any:
        if not Path(value).is_file() and not validators.url(value):
            raise ValueError(WRONG_COVERAGE_FILE_MSG)

        return value


class SampleCreate(SampleBase):
    case_name: str


class Sample(SampleBase):
    created_at: datetime
    id: int

    class Config:
        orm_mode = True


class Case(CaseBase):
    id: int
    samples: List = []

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
    completeness: Dict = Field(default_factory=dict)
    ensembl_gene_id: Optional[str]
    end: Optional[int]
    hgnc_id: Optional[int]
    hgnc_symbol: Optional[str]
    interval_id: Optional[int]
    mean_coverage: Dict = Field(default_factory=dict)
    start: Optional[int]


class SampleGeneIntervalQuery(BaseModel):
    build: Builds
    completeness_thresholds: Optional[List[int]]
    ensembl_gene_ids: Optional[List[str]]
    hgnc_gene_ids: Optional[List[int]]
    hgnc_gene_symbols: Optional[List[str]]
    samples: Optional[List[str]]
    case: Optional[str]

    @root_validator(pre=True)
    def check_genes_lists(cls, values):
        nr_provided_gene_lists: int = 0
        for gene_list in [
            values.get("ensembl_gene_ids"),
            values.get("hgnc_gene_ids"),
            values.get("hgnc_gene_symbols"),
        ]:
            if gene_list:
                nr_provided_gene_lists += 1
        if nr_provided_gene_lists != 1:
            raise ValueError(MULTIPLE_GENE_LISTS_NOT_SUPPORTED_MSG)
        return values

    @root_validator(pre=True)
    def check_sample_input(cls, values):
        case = values.get("case", "") != ""
        samples = bool(values.get("samples", []))
        if case == samples:
            raise ValueError(AMBIGUOUS_SAMPLES_INPUT)

        return values
