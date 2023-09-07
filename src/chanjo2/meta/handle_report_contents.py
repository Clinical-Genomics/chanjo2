import logging
from collections import OrderedDict
from statistics import mean
from typing import List, Dict, Tuple, Union

from pyd4 import D4File
from sqlmodel import Session

from chanjo2.crud.intervals import get_genes
from chanjo2.crud.samples import get_sample
from chanjo2.meta.handle_d4 import get_samples_sex_metrics, get_sample_interval_coverage
from chanjo2.models.pydantic_models import (
    ReportQuery,
    ReportQuerySample,
    SampleSexRow,
    GeneCoverage,
    IntervalType,
)
from chanjo2.models.sql_models import Exon as SQLExon
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Sample as SQLSample
from chanjo2.models.sql_models import Transcript as SQLTranscript

LOG = logging.getLogger("uvicorn.access")

INTERVAL_TYPE_SQL_TYPE: Dict[IntervalType, Union[SQLGene, SQLTranscript, SQLExon]] = {
    IntervalType.GENES: SQLGene,
    IntervalType.TRANSCRIPTS: SQLTranscript,
    IntervalType.EXONS: SQLExon,
}


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
    samples_d4_files: List[Tuple[str, D4File]] = [
        (sample.name, D4File(sample.coverage_file_path)) for sample in query.samples
    ]
    genes: List[SQLGene] = get_genes(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )
    samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
        sample: get_sample_interval_coverage(
            db=session,
            d4_file=d4_file,
            genes=genes,
            interval_type=INTERVAL_TYPE_SQL_TYPE[query.interval_type],
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file in samples_d4_files
    }

    data: Dicr = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "panel_name": query.panel_name,
            "default_level": query.default_level,
        },
        "sex_rows": get_report_sex_rows(
            samples=query.samples, samples_d4_files=samples_d4_files
        ),
        "completeness_rows": get_report_completeness_rows(
            samples_coverage_stats=samples_coverage_stats,
            levels=query.completeness_thresholds,
        ),
    }
    return data


def get_report_completeness_rows(
    samples_coverage_stats: Dict[str, List[GeneCoverage]], levels: List[int]
):
    """Create and return the contents for the samples' coverage completeness rows in the coverage report"""

    completeness_rows: List[str, Dict[str, float]] = []

    for sample, interval_stats in samples_coverage_stats.items():
        sample_stats: Dict[str, List[float]] = {"mean_coverage": []}
        for level in levels:
            sample_stats[f"completeness_{level}"]: List[float] = []

        for interval in interval_stats:
            sample_stats["mean_coverage"].append(interval.mean_coverage)
            for level in levels:
                sample_stats[f"completeness_{level}"].append(
                    interval.completeness[level]
                )

        completeness_row: Dict[str, float] = {}
        for completeness_key, completeness_values in sample_stats.items():
            completeness_row[completeness_key] = (
                round((mean(completeness_values) * 100), 2)
                if completeness_values
                else 0
            )

        completeness_rows.append((sample, completeness_row))

    return completeness_rows


def get_report_sex_rows(
    samples: List[ReportQuerySample], samples_d4_files: List[Tuple[str, D4File]]
) -> List[Dict]:
    """Create and return the contents for the sample sex lines in the coverage report."""
    sample_sex_rows: D4FileList = []
    for sample in samples:
        for identifier, d4_file in samples_d4_files:
            if identifier != sample.name:
                continue

        sample_sex_metrics: Dict = get_samples_sex_metrics(d4_file=d4_file)

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


def get_ordered_levels(threshold_levels: List[int]) -> OrderedDict:
    """Returns the coverage threshold levels as an ordered dictionary."""
    report_levels = OrderedDict()
    for threshold in sorted(threshold_levels):
        report_levels[threshold] = f"completeness_{threshold}"
    return report_levels
