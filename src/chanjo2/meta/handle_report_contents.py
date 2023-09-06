import logging
from collections import OrderedDict
from typing import List, Dict, Tuple

from pyd4 import D4File
from sqlmodel import Session

from chanjo2.crud.intervals import get_genes
from chanjo2.crud.samples import get_sample
from chanjo2.meta.handle_d4 import get_samples_sex_metrics
from chanjo2.models.pydantic_models import ReportQuery, ReportQuerySample, SampleSexRow
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

    data: Dicr = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "panel_name": query.panel_name,
            "default_level": query.default_level,
        },
        "sex_rows": get_report_sex_rows(
            samples=query.samples, samples_d4_files=samples_d4_files
        ),
        "completeness_rows": [],
    }
    return data


def get_report_completeness_rows():
    """Create and return the contents for the samples' coverage completeness rows in the coverage report"""
    return []


def get_report_sex_rows(
    samples: List[ReportQuerySample], samples_d4_files: List[Tuple[str, D4File]]
) -> List[Dict]:
    """Create and return the contents for the sample sex lines in the coverage report."""
    sample_sex_rows: D4FileList = []
    for sample in samples:
        for _, d4_file in samples_d4_files:
            if _ != sample.name:
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
    for threshold in sorted(threshold_levels, reverse=True):
        report_levels[threshold] = f"completeness_{threshold}"
    return report_levels
