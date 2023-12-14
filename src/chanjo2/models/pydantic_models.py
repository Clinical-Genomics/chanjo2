import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import validators
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import SettingsConfigDict

from chanjo2.constants import (
    AMBIGUOUS_SAMPLES_INPUT,
    DEFAULT_COMPLETENESS_LEVELS,
    MULTIPLE_GENE_LISTS_NOT_SUPPORTED_MSG,
    WRONG_COVERAGE_FILE_MSG,
)

LOG = logging.getLogger("uvicorn.access")


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


class TranscriptTag(str, Enum):
    REFSEQ_MRNA = "refseq_mrna"
    REFSEQ_NCRNA = "refseq_ncrna"
    REFSEQ_MANE_SELECT = "refseq_mane_select"
    REFSEQ_MANE_PLUS_CLINICAL = "refseq_mane_plus_clinical"


class Sex(str, Enum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


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

    @field_validator("coverage_file_path", mode="before")
    def validate_coverage_path(cls, value: str) -> Any:
        if not Path(value).is_file() and not validators.url(value):
            raise ValueError(WRONG_COVERAGE_FILE_MSG)

        return value


class SampleCreate(SampleBase):
    case_name: str


class Sample(SampleBase):
    created_at: datetime
    id: int
    model_config = SettingsConfigDict(from_attributes=True)


class Case(CaseBase):
    id: int
    samples: List = []
    model_config = SettingsConfigDict(from_attributes=True)


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
    ensembl_ids: Optional[List[str]] = None
    hgnc_ids: Optional[List[int]] = None
    hgnc_symbols: Optional[List[str]] = None
    limit: Optional[int] = 100


class GeneIntervalQuery(GeneQuery):
    ensembl_gene_ids: Optional[List[str]] = None


class Gene(IntervalBase):
    id: int


class TranscriptBase(IntervalBase):
    build: Builds
    ensembl_id: str
    ensembl_gene_id: str
    refseq_mrna: Optional[str] = None
    refseq_mrna_pred: Optional[str] = None
    refseq_ncrna: Optional[str] = None
    refseq_mane_select: Optional[str] = None
    refseq_mane_plus_clinical: Optional[str] = None


class Transcript(TranscriptBase):
    id: int


class ExonBase(IntervalBase):
    build: Builds
    ensembl_id: str
    ensembl_gene_id: str
    ensembl_transcript_id: str


class Exon(IntervalBase):
    id: int


class IntervalCoverage(BaseModel):
    mean_coverage: float
    completeness: Optional[Dict] = Field(default_factory=dict)
    interval_id: Optional[str] = None
    interval_type: Optional[IntervalType] = IntervalType.CUSTOM


class GeneCoverage(IntervalCoverage):
    inner_intervals: List[IntervalCoverage] = []  # Transcripts or exons
    hgnc_id: Optional[int] = None
    hgnc_symbol: Optional[str] = None
    ensembl_gene_id: Optional[str] = None


class FileCoverageBaseQuery(BaseModel):
    coverage_file_path: str


class FileCoverageQuery(FileCoverageBaseQuery):
    chromosome: str
    start: Optional[int] = None
    end: Optional[int] = None
    completeness_thresholds: Optional[List[int]] = []


class FileCoverageIntervalsFileQuery(FileCoverageBaseQuery):
    intervals_bed_path: str
    completeness_thresholds: Optional[List[int]] = []


class SampleGeneIntervalQuery(BaseModel):
    build: Builds
    completeness_thresholds: Optional[List[int]] = []
    ensembl_gene_ids: Optional[List[str]] = None
    hgnc_gene_ids: Optional[List[int]] = None
    hgnc_gene_symbols: Optional[List[str]] = None
    samples: Optional[List[str]] = None
    case: Optional[str] = None

    @model_validator(mode="before")
    def check_genes_lists(cls, values: dict):
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

    @model_validator(mode="before")
    def check_sample_input(cls, values: dict):
        case = values.get("case")
        samples = values.get("samples")
        if case and samples:
            raise ValueError(AMBIGUOUS_SAMPLES_INPUT)

        return values


## Coverage and  overview report - related models ###


class ReportQuerySample(BaseModel):
    name: str
    coverage_file_path: Optional[str] = None
    case_name: Optional[str] = None
    analysis_date: Optional[datetime] = datetime.now()


class ReportQuery(BaseModel):
    build: Builds
    completeness_thresholds: Optional[List[int]] = DEFAULT_COMPLETENESS_LEVELS
    ensembl_gene_ids: Optional[List[str]] = None
    hgnc_gene_ids: Optional[List[int]] = None
    hgnc_gene_symbols: Optional[List[str]] = None
    interval_type: IntervalType
    default_level: int = 10
    panel_name: Optional[str] = "Custom panel"
    case_display_name: Optional[str] = None
    samples: List[ReportQuerySample]

    @field_validator("samples", mode="before")
    def samples_validator(cls, sample_list):
        if isinstance(sample_list, str):
            return json.loads(sample_list.replace("'", '"'))
        return sample_list


class GeneReportForm(BaseModel):
    build: Builds
    completeness_thresholds: Optional[List[int]] = DEFAULT_COMPLETENESS_LEVELS
    hgnc_gene_id: int
    default_level: int = 10
    samples: List[ReportQuerySample]
    interval_type: IntervalType

    @field_validator("samples", mode="before")
    def samples_validator(cls, sample_list):
        if isinstance(sample_list, str):
            return json.loads(sample_list.replace("'", '"'))
        return sample_list

    @field_validator("completeness_thresholds", mode="before")
    def coverage_thresholds_validator(cls, completeness_thresholds: str):
        thresholds: List[str] = completeness_thresholds.split(",")
        return [int(threshold.strip()) for threshold in thresholds]


class SampleSexRow(BaseModel):
    sample: str
    case: Optional[str]
    analysis_date: datetime
    predicted_sex: str
    x_coverage: float
    y_coverage: float
