from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_genes, get_hgnc_gene, set_sql_intervals
from chanjo2.crud.samples import get_sample
from chanjo2.meta.handle_d4 import (
    get_report_sample_interval_coverage,
    get_sample_interval_coverage,
    get_samples_sex_metrics,
)
from chanjo2.models import SQLExon, SQLGene, SQLSample, SQLTranscript
from chanjo2.models.pydantic_models import (
    GeneCoverage,
    GeneReportForm,
    IntervalType,
    ReportQuery,
    ReportQuerySample,
    SampleSexRow,
    TranscriptTag,
)

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
    query: ReportQuery, session: Session, is_overview: Optional[bool] = False
) -> Dict:
    """Return the information that will be displayed in the coverage report or in the genes overview report.."""

    set_samples_coverage_files(session=session, samples=query.samples)

    genes: List[SQLGene] = get_genes(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )

    data: Dict = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "panel_name": query.panel_name,
            "default_level": query.default_level,
            "interval_type": query.interval_type.value,
            "case_name": query.case_display_name,
            "hgnc_gene_ids": [gene.hgnc_id for gene in genes]
            or query.hgnc_gene_ids
            or query.hgnc_gene_symbols
            or query.ensembl_gene_ids,
            "build": query.build.value,
            "completeness_thresholds": query.completeness_thresholds,
            "samples": [_serialize_sample(sample) for sample in query.samples],
        },
        "completeness_rows": [],
        "incomplete_coverage_rows": [],
        "default_level_completeness_rows": [],
    }

    # Add coverage_report - specific data
    data["sex_rows"] = get_report_sex_rows(samples=query.samples)

    data["errors"] = [
        get_missing_genes_from_db(
            sql_genes=genes,
            ensembl_ids=query.ensembl_gene_ids,
            hgnc_ids=query.hgnc_gene_ids,
            hgnc_symbols=query.hgnc_gene_symbols,
        )
    ]

    gene_ids_mapping: Dict[str, dict] = {
        gene.ensembl_id: {"hgnc_id": gene.hgnc_id, "hgnc_symbol": gene.hgnc_symbol}
        for gene in genes
    }

    if not gene_ids_mapping:
        return data

    sql_intervals = set_sql_intervals(
        db=session,
        interval_type=INTERVAL_TYPE_SQL_TYPE[query.interval_type],
        genes=genes,
        transcript_tags=[TranscriptTag.REFSEQ_MRNA],
    )

    intervals_coords: List[str] = [
        f"{interval.chromosome}\t{interval.start}\t{interval.stop}"
        for interval in sql_intervals
    ]

    for sample in query.samples:
        get_report_sample_interval_coverage(
            d4_file_path=sample.coverage_file_path,
            sample_name=sample.name,
            gene_ids_mapping=gene_ids_mapping,
            sql_intervals=sql_intervals,
            intervals_coords=intervals_coords,
            completeness_thresholds=(
                [query.default_level] if is_overview else query.completeness_thresholds
            ),
            default_threshold=query.default_level,
            report_data=data,
        )
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


def get_report_sex_rows(samples: List[ReportQuerySample]) -> List[Dict]:
    """Create and return the contents for the sample sex lines in the coverage report."""
    sample_sex_rows: D4FileList = []
    for sample in samples:
        sample_sex_metrics: Dict = get_samples_sex_metrics(
            d4_file_path=sample.coverage_file_path
        )

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

    gene: SQLGene = get_hgnc_gene(
        build=form_data.build, hgnc_id=form_data.hgnc_gene_id, db=session
    )
    if gene is None:
        return gene_stats
    gene_stats["gene"] = gene

    samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
        sample.name: get_sample_interval_coverage(
            db=session,
            d4_file_path=sample.coverage_file_path,
            genes=[gene],
            interval_type=INTERVAL_TYPE_SQL_TYPE[form_data.interval_type],
            completeness_thresholds=form_data.completeness_thresholds,
        )
        for sample in form_data.samples
    }
    gene_stats["samples_coverage_stats_by_interval"] = (
        get_gene_coverage_stats_by_interval(coverage_by_sample=samples_coverage_stats)
    )
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
