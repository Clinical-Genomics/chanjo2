import logging
from collections import OrderedDict
from statistics import mean
from typing import Dict, List, Optional, Set, Tuple, Union

from pyd4 import D4File
from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_genes, get_hgnc_gene
from chanjo2.crud.samples import get_sample
from chanjo2.meta.handle_d4 import get_sample_interval_coverage, get_samples_sex_metrics
from chanjo2.models import SQLExon, SQLGene, SQLSample, SQLTranscript
from chanjo2.models.pydantic_models import (
    GeneCoverage,
    GeneReportForm,
    IntervalType,
    ReportQuery,
    ReportQuerySample,
    SampleSexRow,
)

LOG = logging.getLogger("uvicorn.access")

INTERVAL_TYPE_SQL_TYPE: Dict[IntervalType, Union[SQLGene, SQLTranscript, SQLExon]] = {
    IntervalType.GENES: SQLGene,
    IntervalType.TRANSCRIPTS: SQLTranscript,
    IntervalType.EXONS: SQLExon,
}


#### Functions used by all reports ####


def get_ordered_levels(threshold_levels: List[int]) -> OrderedDict:
    """Returns the coverage threshold levels as an ordered dictionary."""
    report_levels = OrderedDict()
    for threshold in sorted(threshold_levels):
        report_levels[threshold] = f"completeness_{threshold}"
    return report_levels


def set_samples_coverage_files(session: Session, samples: List[ReportQuerySample]):
    """Set path to coverage file for each sample in the samples list."""

    for sample in samples:
        if sample.coverage_file_path:  # if path to d4 is provided in the query
            continue
        else:  # fetch it from the database
            sql_sample: SQLSample = get_sample(db=session, sample_name=sample.name)
            sample.coverage_file_path = sql_sample.coverage_file_path


def _serialize_sample(sample: ReportQuerySample) -> Dict[str, str]:
    """Convert a ReportQuerySample object to an easily serialized dictionary."""
    return {
        "name": sample.name,
        "case_name": sample.case_name,
        "coverage_file_path": sample.coverage_file_path,
        "analysis_date": str(sample.analysis_date),
    }


def get_report_data(
    query: ReportQuery, session: Session, is_overview_report: bool
) -> Dict:
    """Return the information that will be displayed in the coverage report or in the genes overview report.."""

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
            transcript_tags=["refseq_mrna"],
        )
        for sample, d4_file in samples_d4_files
    }

    data: Dict = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "panel_name": query.panel_name,
            "default_level": query.default_level,
            "interval_type": query.interval_type.value,
            "case_name": query.case_display_name,
            "hgnc_gene_ids": [gene.hgnc_id for gene in genes],
            "build": query.build.value,
            "completeness_thresholds": query.completeness_thresholds,
            "samples": [_serialize_sample(sample) for sample in query.samples],
        },
    }

    if is_overview_report:
        data["incomplete_coverage_rows"] = get_genes_overview_incomplete_coverage_rows(
            samples_coverage_stats=samples_coverage_stats,
            interval_type=query.interval_type.value,
            cov_level=query.default_level,
        )
        return data

    # Add coverage_report - specific data
    data["sex_rows"] = get_report_sex_rows(
        samples=query.samples, samples_d4_files=samples_d4_files
    )
    data["completeness_rows"] = get_report_completeness_rows(
        samples_coverage_stats=samples_coverage_stats,
        levels=query.completeness_thresholds,
    )
    data["default_level_completeness_rows"] = get_report_level_completeness_rows(
        samples_coverage_stats=samples_coverage_stats, level=query.default_level
    )
    data["errors"] = [
        get_missing_genes_from_db(
            sql_genes=genes,
            ensembl_ids=query.ensembl_gene_ids,
            hgnc_ids=query.hgnc_gene_ids,
            hgnc_symbols=query.hgnc_gene_symbols,
        )
    ]
    return data


#### Functions used to create coverage report data


def get_missing_genes_from_db(
    sql_genes: List[SQLGene],
    ensembl_ids: Optional[List[str]] = [],
    hgnc_ids: Optional[List[int]] = [],
    hgnc_symbols: Optional[List[str]] = [],
) -> Tuple[str, List[Union[str, int]]]:
    """Return queried genes that are not found in the database."""

    if ensembl_ids:
        sql_genes_ids = [gene.ensembl_id for gene in sql_genes]
    elif hgnc_ids:
        sql_genes_ids = [gene.hgnc_id for gene in sql_genes]
    else:
        sql_genes_ids = [gene.hgnc_symbol for gene in sql_genes]

    query_ids: List[Union[str, int]] = ensembl_ids or hgnc_ids or hgnc_symbols
    return "Gene IDs not found in the database", list(
        set(query_ids) - set(sql_genes_ids)
    )


def get_report_level_completeness_rows(
    samples_coverage_stats: Dict[str, List[GeneCoverage]], level: int
) -> List[Tuple[str, float, str, List[str]]]:
    """Create and return the contents of the coverage stats row at the default threshold level and incompletely covered genes."""
    default_level_rows: List[Tuple[str, float, str]] = []

    for sample, genes_stats in samples_coverage_stats.items():
        nr_inner_intervals: int = 0
        covered_inner_intervals: int = 0
        incompletely_covered_genes: Set[str] = set()
        for gene_stats in genes_stats:
            intervals = gene_stats.inner_intervals or [gene_stats]
            for interval in intervals:
                nr_inner_intervals += 1
                if interval.mean_coverage >= level:
                    covered_inner_intervals += 1
                else:
                    incompletely_covered_genes.add(
                        gene_stats.hgnc_symbol or gene_stats.hgnc_id
                    )

        intervals_covered_percent: float = (
            round((covered_inner_intervals / nr_inner_intervals * 100), 2)
            if covered_inner_intervals > 0
            else 0
        )
        nr_not_covered_intervals: str = (
            f"{nr_inner_intervals - covered_inner_intervals}/{nr_inner_intervals}"
        )
        default_level_rows.append(
            (
                sample,
                intervals_covered_percent,
                nr_not_covered_intervals,
                sorted(incompletely_covered_genes),
            )
        )

    return default_level_rows


def get_report_completeness_rows(
    samples_coverage_stats: Dict[str, List[GeneCoverage]], levels: List[int]
) -> List[Tuple[str, Dict[str, float]]]:
    """Create and return the contents for the samples' coverage completeness rows in the coverage report."""

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


#### Functions used to create a genes overview report ####


def _get_incomplete_gene_coverage_overview_line(
    hgnc_symbol: str, hgnc_id: int, interval_id: str, sample: str, completeness: float
) -> Optional[Tuple[Union[str, int, float]]]:
    """Return a gene overview report line if the interval is not fully covered at the given threshold."""
    if completeness < 1:
        return (hgnc_symbol, hgnc_id, interval_id, sample, round(completeness, 2))


def _remove_none_elements(tuple_list: List[Tuple] = []) -> List[Tuple]:
    """Remove rows which are set to None in a list of genes overview rows."""
    return [tuple for tuple in tuple_list if tuple is not None]


def get_genes_overview_incomplete_coverage_rows(
    samples_coverage_stats: Dict[str, List[GeneCoverage]],
    interval_type: IntervalType,
    cov_level: int,
) -> List[Tuple[str, int, float]]:
    """Return incomplete gene coverage rows for given coverage level."""

    genes_overview_rows: List[str] = []

    for sample_name, genes_cov_stats_list in samples_coverage_stats.items():
        for gene_cov_stats in genes_cov_stats_list:
            if interval_type == IntervalType.GENES:
                completeness_at_level: float = gene_cov_stats.completeness.get(
                    cov_level
                )
                overview_line: Optional[
                    List[str]
                ] = _get_incomplete_gene_coverage_overview_line(
                    hgnc_symbol=gene_cov_stats.hgnc_symbol,
                    hgnc_id=gene_cov_stats.hgnc_id,
                    interval_id=gene_cov_stats.hgnc_id,
                    sample=sample_name,
                    completeness=completeness_at_level,
                )

                genes_overview_rows.append(overview_line)

            else:
                for inner_interval_stats in gene_cov_stats.inner_intervals:
                    completeness_at_level: float = (
                        inner_interval_stats.completeness.get(cov_level)
                    )
                    overview_line: Optional[
                        List[str]
                    ] = _get_incomplete_gene_coverage_overview_line(
                        hgnc_symbol=gene_cov_stats.hgnc_symbol,
                        hgnc_id=gene_cov_stats.hgnc_id,
                        interval_id=inner_interval_stats.interval_id,
                        sample=sample_name,
                        completeness=completeness_at_level,
                    )

                    genes_overview_rows.append(overview_line)

    return _remove_none_elements(tuple_list=genes_overview_rows)


#### Functions used to create a gene overview report ####


def get_gene_overview_coverage_stats(form_data: GeneReportForm, session: Session):
    """Returns coverage stats over the intervals sof one gene for one or more samples."""

    gene_stats = {
        "levels": get_ordered_levels(
            threshold_levels=form_data.completeness_thresholds
        ),
        "interval_type": form_data.interval_type.value,
        "samples_coverage_stats_by_interval": {},
    }

    set_samples_coverage_files(session=session, samples=form_data.samples)

    samples_d4_files: List[Tuple[str, D4File]] = [
        (sample.name, D4File(sample.coverage_file_path)) for sample in form_data.samples
    ]

    gene: SQLGene = get_hgnc_gene(
        build=form_data.build, hgnc_id=form_data.hgnc_gene_id, db=session
    )
    if gene is None:
        return gene_stats
    gene_stats["gene"] = gene

    samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
        sample: get_sample_interval_coverage(
            db=session,
            d4_file=d4_file,
            genes=[gene],
            interval_type=INTERVAL_TYPE_SQL_TYPE[form_data.interval_type],
            completeness_thresholds=form_data.completeness_thresholds,
        )
        for sample, d4_file in samples_d4_files
    }
    gene_stats[
        "samples_coverage_stats_by_interval"
    ] = get_gene_coverage_stats_by_interval(coverage_by_sample=samples_coverage_stats)
    return gene_stats


def get_gene_coverage_stats_by_interval(
    coverage_by_sample: Dict[str, List[GeneCoverage]]
) -> Dict[str, List[Tuple]]:
    """Arrange coverage stats by interval id instead of by sample."""

    intervals_stats: Dict[str, List] = {}

    for sample, stats in coverage_by_sample.items():
        for gene_interval in stats:
            for inner_interval in gene_interval.inner_intervals:
                if inner_interval.interval_id in intervals_stats:
                    intervals_stats[inner_interval.interval_id].append(
                        (
                            sample,
                            inner_interval.mean_coverage,
                            inner_interval.completeness,
                        )
                    )
                else:
                    intervals_stats[inner_interval.interval_id] = [
                        (
                            sample,
                            inner_interval.mean_coverage,
                            inner_interval.completeness,
                        )
                    ]

    return intervals_stats
