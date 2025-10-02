import json
import os
from datetime import datetime
from enum import Enum
from os.path import isfile
from typing import Dict, List, Optional, Union

import validators
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.datastructures import FormData

from chanjo2.constants import (
    DEFAULT_COMPLETENESS_LEVELS,
    DEFAULT_COVERAGE_LEVEL,
    GENE_LISTS_NOT_SUPPORTED_MSG,
    HTTP_D4_COMPLETENESS_ERROR,
    WRONG_COVERAGE_FILE_MSG,
)


def validate_url_and_completeness(
    d4_file: str, completeness_thresholds: Optional[List[int]]
):
    """Raise error if d4 file is HTTP file and completeness thresholds are present."""
    if not completeness_thresholds:
        return
    if is_valid_url(d4_file) is False:
        return
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=HTTP_D4_COMPLETENESS_ERROR,
    )


def is_valid_url(value: str) -> bool:
    """Makes sure that a string is formatted as an URL."""
    try:
        return bool(validators.url(value))
    except Exception:
        return False


def default_report_coverage_levels() -> List[int]:
    """Sets the coverage thresholds to be used for report metrics whenever a request doesn't contain 'completeness_thresholds' values."""
    if os.getenv("REPORT_COVERAGE_LEVELS"):
        return json.loads(os.getenv("REPORT_COVERAGE_LEVELS"))
    return DEFAULT_COMPLETENESS_LEVELS


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

    @staticmethod
    def get_enum_values() -> List[str]:
        """Returns the values of the available interval types."""
        return [member.value for member in IntervalType]


class TranscriptTag(str, Enum):
    REFSEQ_MRNA = "refseq_mrna"
    REFSEQ_NCRNA = "refseq_ncrna"
    REFSEQ_MANE_SELECT = "refseq_mane_select"
    REFSEQ_MANE_PLUS_CLINICAL = "refseq_mane_plus_clinical"


class Sex(str, Enum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


class IntervalBase(BaseModel):
    chromosome: str
    start: int
    stop: int


class Interval(IntervalBase):
    id: int


class GeneBase(IntervalBase):
    build: Builds
    ensembl_ids: List[str]
    hgnc_id: Optional[int]
    hgnc_symbol: Optional[str]

    model_config = ConfigDict(from_attributes=True)


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
    rank_in_transcript: int


class Exon(IntervalBase):
    id: int


class IntervalCoverage(BaseModel):
    mean_coverage: float
    completeness: Optional[Dict] = Field(default_factory=dict)
    interval_id: Optional[str] = None
    interval_type: Optional[IntervalType] = IntervalType.CUSTOM


class GeneCoverage(IntervalCoverage):
    inner_intervals: List[IntervalCoverage] = Field(default_factory=list)
    hgnc_id: Optional[int] = None
    hgnc_symbol: Optional[str] = None
    ensembl_gene_id: Optional[str] = None


class FileCoverageBaseQuery(BaseModel):
    coverage_file_path: str


class FileCoverageQuery(FileCoverageBaseQuery):
    chromosome: str
    start: Optional[int] = None
    end: Optional[int] = None
    completeness_thresholds: Optional[List[int]] = Field(default_factory=list)
    coverage_file_path: str

    @field_validator("coverage_file_path", mode="after")
    def coverage_file_path_validator(cls, coverage_file_path):
        if isfile(coverage_file_path) or is_valid_url(coverage_file_path):
            return coverage_file_path
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=WRONG_COVERAGE_FILE_MSG)

    @model_validator(mode="after")
    def coverage_path_completeness_validator(self):
        """Completeness computation is not supported for d4 files over HTTP."""
        validate_url_and_completeness(
            d4_file=self.coverage_file_path,
            completeness_thresholds=self.completeness_thresholds,
        )
        return self


class FileCoverageIntervalsFileQuery(FileCoverageBaseQuery):
    intervals_bed_path: str
    completeness_thresholds: Optional[List[int]] = Field(default_factory=list)
    coverage_file_path: str

    @field_validator("coverage_file_path", mode="after")
    def coverage_file_path_validator(cls, coverage_file_path):
        if isfile(coverage_file_path) or is_valid_url(coverage_file_path):
            return coverage_file_path
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=WRONG_COVERAGE_FILE_MSG)

    @model_validator(mode="after")
    def coverage_path_completeness_validator(self):
        validate_url_and_completeness(
            d4_file=self.coverage_file_path,
            completeness_thresholds=self.completeness_thresholds,
        )
        return self


class CoverageSummaryQuerySample(BaseModel):
    name: str
    coverage_file_path: str


class CoverageSummaryQuery(BaseModel):
    build: Builds
    samples: List[CoverageSummaryQuerySample]
    hgnc_gene_ids: List[int]
    coverage_threshold: int
    interval_type: IntervalType

    @model_validator(mode="after")
    def check_no_http_cov_files(self):
        """Completeness computation, which is performed downstream, is not supported for d4 files over HTTP."""
        for sample in self.samples:
            if is_valid_url(sample.coverage_file_path):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=HTTP_D4_COMPLETENESS_ERROR,
                )
        return self


class ReportQuerySample(BaseModel):
    name: str
    coverage_file_path: Optional[str] = None
    case_name: Optional[str] = None
    analysis_date: Optional[datetime] = Field(default_factory=datetime.now)

    @field_validator("coverage_file_path", mode="after")
    def coverage_file_path_validator(cls, coverage_file_path):
        if coverage_file_path is None:
            return coverage_file_path
        if isfile(coverage_file_path) or is_valid_url(coverage_file_path):
            return coverage_file_path
        raise ValueError(WRONG_COVERAGE_FILE_MSG)


class ReportQuery(BaseModel):
    build: Builds
    completeness_thresholds: Optional[List[int]] = Field(
        default_factory=default_report_coverage_levels
    )
    ensembl_gene_ids: Optional[List[str]] = None
    hgnc_gene_ids: Optional[List[int]] = None
    hgnc_gene_symbols: Optional[List[str]] = None
    interval_type: IntervalType
    default_level: int = DEFAULT_COVERAGE_LEVEL
    panel_name: Optional[str] = None
    case_display_name: Optional[str] = None
    samples: List[ReportQuerySample]

    @field_validator("samples", mode="before")
    def samples_validator(cls, sample_list):
        if isinstance(sample_list, str):
            return json.loads(sample_list.replace("'", '"'))
        return sample_list

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
        if nr_provided_gene_lists > 1:
            raise ValueError(GENE_LISTS_NOT_SUPPORTED_MSG)
        return values

    @model_validator(mode="after")
    def coverage_paths_completeness_validator(self):
        """Completeness computation is not supported for d4 files over HTTP. Check each sample."""
        for sample in self.samples:
            validate_url_and_completeness(
                d4_file=sample.coverage_file_path,
                completeness_thresholds=self.completeness_thresholds,
            )
        return self

    @staticmethod
    def comma_sep_values_to_list(
        comma_sep_values: Optional[str], items_format: Union[str, int]
    ) -> Optional[List[Union[str, int]]]:
        """Helper function that formats list of strings or integers passed by a form as comma separated values."""
        if comma_sep_values is None:
            return
        if items_format == str:
            return [item.strip() for item in comma_sep_values.split(",")]
        else:
            return [int(item.strip()) for item in comma_sep_values.split(",")]

    @staticmethod
    def set_query_genes(form_data: FormData):
        query_genes = {
            "ensembl_gene_ids": [],
            "hgnc_gene_ids": [],
            "hgnc_gene_symbols": [],
        }
        """Helper function that collects form data from report page requests and sets the right gene IDs/values in the query."""
        for gene_ids_key in query_genes.keys():
            if bool(form_data.get(gene_ids_key)) is False:
                continue
            id_values: List[Union[str, int]] = [
                item.strip() for item in form_data.get(gene_ids_key).split(",")
            ]
            for value in id_values:
                if value.isdigit():
                    query_genes["hgnc_gene_ids"].append(int(value))
                elif value.startswith("ENSG"):
                    query_genes["ensembl_gene_ids"].append(value)
                else:
                    query_genes["hgnc_gene_symbols"].append(value)
        return query_genes

    @classmethod
    def as_form(cls, form_data: FormData) -> "ReportQuery":
        query_genes = cls.set_query_genes(form_data)
        return cls(
            build=form_data.get("build"),
            completeness_thresholds=(
                cls.comma_sep_values_to_list(
                    form_data.get("completeness_thresholds"), int
                )
                if form_data.get("completeness_thresholds")
                else default_report_coverage_levels()
            ),
            ensembl_gene_ids=query_genes["ensembl_gene_ids"],
            hgnc_gene_ids=query_genes["hgnc_gene_ids"],
            hgnc_gene_symbols=query_genes["hgnc_gene_symbols"],
            interval_type=form_data.get("interval_type"),
            default_level=int(form_data.get("default_level") or DEFAULT_COVERAGE_LEVEL),
            panel_name=form_data.get("panel_name"),
            case_display_name=form_data.get("case_display_name"),
            samples=form_data.get("samples"),
        )


class GeneReportForm(BaseModel):
    build: Builds
    completeness_thresholds: Optional[List[int]] = Field(
        default_factory=default_report_coverage_levels
    )
    hgnc_gene_id: int
    default_level: int = DEFAULT_COVERAGE_LEVEL
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

    @field_validator("interval_type", mode="before")
    def interval_type_validator(cls, interval_type: IntervalType) -> IntervalType:
        if interval_type == IntervalType.GENES:
            return IntervalType.TRANSCRIPTS
        return interval_type

    @model_validator(mode="after")
    def check_thresholds_not_with_url_d4(self):
        if self.completeness_thresholds:
            for sample in self.samples:
                if is_valid_url(sample.coverage_file_path):
                    raise HTTPException(
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=HTTP_D4_COMPLETENESS_ERROR,
                    )
        return self


class SampleSexRow(BaseModel):
    sample: str
    case: Optional[str]
    analysis_date: datetime
    predicted_sex: str
    x_coverage: float
    y_coverage: float
