import logging
from collections import OrderedDict
from typing import List, Dict

from pyd4 import D4File
from sqlmodel import Session

from chanjo2.crud.intervals import get_genes
from chanjo2.crud.samples import get_sample
from chanjo2.meta.handle_d4 import (
    get_genes_coverage_completeness,
    get_gene_interval_coverage_completeness,
)
from chanjo2.meta.handle_d4 import get_samples_sex_metrics
from chanjo2.models.pydantic_models import (
    ReportQuery,
    ReportQuerySample,
    SampleSexRow,
    IntervalType,
)
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Sample as SQLSample

LOG = logging.getLogger("uvicorn.access")


def set_samples_coverage_files(session: Session, samples: List[ReportQuerySample]):
    """Set path to coverage file for each sample in the samples list."""

    for sample in samples:
        if sample.coverage_file_path:  # if path to d4 is provided in the query
            continue
        else:  # fetch it from the database
            sql_sample: SQLSample = get_sample(db=session, sample_name=sample)
            sample.coverage_file_path = sql_sample.coverage_file_path


def get_report_data(query: ReportQuery, session: Session) -> Dict:
    """Return the information that will be displayed in the coverage report."""

    set_samples_coverage_files(session=session, samples=query.samples)
    samples_d4_files: Dict[str, D4File] = {
        sample.name: D4File(sample.coverage_file_path) for sample in query.samples
    }
    genes: List[SQLGene] = get_genes(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )
    data: Dicr = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "panel_name": query.panel_name,
            "default_level": query.default_level,
        },
        "sex_rows": get_report_sex_rows(query.samples, samples_d4_files),
        "completeness_rows": get_sample_completeness_by_level(
            levels=sorted(query.completeness_thresholds),
            genes=genes,
            interval_type=query.interval_type,
            samples_d4_files=samples_d4_files,
            session=session,
        ),
    }
    return data


def get_report_sex_rows(
    samples: List[ReportQuerySample], samples_d4_files: Dict[str, D4File]
) -> List[Dict]:
    """Create and return the contents for the sample sex lines in the coverage report."""
    sample_sex_rows: D4FileList = []
    for sample in samples:
        sample_d4: D4File = samples_d4_files[sample.name]
        sample_sex_metrics: Dict = get_samples_sex_metrics(d4_file=sample_d4)

        sample_sex_row: SampleSexRow = SampleSexRow(
            **{
                "sample": sample.name,
                "case": sample.case_name,
                "analysis_date": sample.analysis_date,
                "predicted_sex": sample_sex_metrics["predicted_sex"],
                "x_coverage": sample_sex_metrics["x_coverage"],
                "y_coverage": sample_sex_metrics["y_coverage"],
            }
        )
        sample_sex_rows.append(sample_sex_row)
    return sample_sex_rows


def get_sample_completeness_by_level(
    levels: List[int],
    genes: List[SQLGene],
    interval_type: IntervalType,
    samples_d4_files: Dict[str, D4File],
    session: Session,
):
    """Returns average coverage and coverage completeness by level for each sample in the query."""

    samples_d4_files_tuples: List[Tuple[str, D4File]] = [
        (sample, d4_file) for sample, d4_file in samples_d4_files.items()
    ]
    if interval_type == IntervalType.GENES:
        coverage_intervals: List[CoverageInterval] = get_genes_coverage_completeness(
            samples_d4_files=samples_d4_files_tuples,
            genes=genes,
            completeness_threholds=levels,
        )
    else:
        coverage_intervals: get_gene_interval_coverage_completeness(
            db=session,
            samples_d4_files=samples_d4_files_tuples,
            genes=genes,
            interval_type=interval_type,
            completeness_threholds=levels,
        )

    LOG.error(coverage_intervals)
    completeness_rows: List[Dict] = []
    for sample in samples_d4_files:
        completeness_row: Dict = {"sample": sample, "avg_cov": ""}

    return coverage_intervals


def get_ordered_levels(threshold_levels: List[int]) -> OrderedDict:
    """Returns the coverage threshold levels as an ordered dictionary."""
    report_levels = OrderedDict()
    for threshold in sorted(threshold_levels):
        report_levels[threshold] = f"completeness_{threshold}"
    return report_levels
