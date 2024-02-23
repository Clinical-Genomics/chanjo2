import logging
from collections import OrderedDict
from typing import Dict, List, Optional, Set, Tuple, Union

from pyd4 import D4File
from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_gene_intervals, get_genes, get_hgnc_gene
from chanjo2.crud.samples import get_sample
from chanjo2.meta.handle_d4 import get_sample_interval_coverage, get_samples_sex_metrics
from chanjo2.meta.handle_tasks import (
    samples_coverage_completeness_multitasker,
    samples_coverage_multitasker,
)
from chanjo2.models import SQLExon, SQLGene, SQLSample, SQLTranscript
from chanjo2.models.pydantic_models import (
    Builds,
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
from statistics import mean

#### Functions used by all reports ####


def get_gene_intervals_coords(
    genes: List[SQLGene],
    interval_type: IntervalType,
    db: Session,
    build: Builds,
) -> Dict[str, List[Tuple[str, Tuple[str, int, int]]]]:
    """Returns a dictionary with gene ensembl IDs as keys and gene intervals (gene / gene transcripts / gene exons) coordinates as values."""

    if interval_type == IntervalType.GENES.value:
        return {
            gene.ensembl_id: [
                (gene.ensembl_id, (gene.chromosome, gene.start, gene.stop))
            ]
            for gene in genes
        }

    gene_intervals_coords: Dict[str, List[Tuple[str, Tuple[str, int, int]]]] = {
        gene.ensembl_id: [] for gene in genes
    }

    intervals: List[Union[SQLTranscript, SQLExon]] = get_gene_intervals(
        db=db,
        build=build,
        ensembl_gene_ids=[gene.ensembl_id for gene in genes],
        interval_type=INTERVAL_TYPE_SQL_TYPE[interval_type],
        transcript_tags=["refseq_mrna"],
    )

    for interval in intervals:
        gene_intervals_coords[interval.ensembl_gene_id].append(
            (interval.ensembl_id, (interval.chromosome, interval.start, interval.stop))
        )

    return gene_intervals_coords


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


#### Functions to create gene coverage report and genes overview report


def set_general_report_data(query: ReportQuery) -> dict:
    """Set general report info from parameters derived from user query."""
    data: Dict = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "panel_name": query.panel_name,
            "default_level": query.default_level,
            "interval_type": query.interval_type.value,
            "case_name": query.case_display_name,
            "build": query.build.value,
            "completeness_thresholds": query.completeness_thresholds,
            "samples": [_serialize_sample(sample) for sample in query.samples],
        },
    }
    return data


def get_report_data(
    query: ReportQuery, session: Session, is_overview_report: bool
) -> Dict:
    """Return the information that will be displayed in the coverage report or in the genes overview report.."""

    set_samples_coverage_files(session=session, samples=query.samples)
    data: dict = set_general_report_data(query=query)

    genes: List[SQLGene] = get_genes(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )

    data["extras"]["hgnc_gene_ids"] = ([gene.hgnc_id for gene in genes],)

    gene_intervals_coords: Dict[str, List[Tuple[str, Tuple[str, int, int]]]] = (
        get_gene_intervals_coords(
            genes=genes,
            interval_type=query.interval_type,
            db=session,
            build=query.build.value,
        )
    )

    coverage_by_sample: Dict[str, List[float]] = samples_coverage_multitasker(
        query=query, gene_intervals_coords=gene_intervals_coords
    )
    coverage_completeness_by_sample: List[Tuple[str, Dict[str, float]]] = (
        samples_coverage_completeness_multitasker(
            query=query, gene_intervals_coords=gene_intervals_coords
        )
    )

    if is_overview_report:
        gene_symbol_ensembl_id_mapping = {
            gene.ensembl_id: gene.hgnc_symbol for gene in genes
        }
        data["incomplete_coverage_rows"] = get_genes_overview_incomplete_coverage_rows(
            coverage_completeness_by_sample=coverage_completeness_by_sample,
            genes_mapping=gene_symbol_ensembl_id_mapping,
            cov_level=query.default_level,
        )
        return data

    data["sex_rows"] = get_report_sex_rows(samples=query.samples)
    data["errors"] = [
        get_missing_genes_from_db(
            sql_genes=genes,
            ensembl_ids=query.ensembl_gene_ids,
            hgnc_ids=query.hgnc_gene_ids,
            hgnc_symbols=query.hgnc_gene_symbols,
        )
    ]

    data["completeness_rows"] = []
    data["default_level_completeness_rows"] = []
    for sample in query.samples:

        nr_fully_covered_intervals: List[float] = []

        sample_stats: dict = {
            f"completeness_{threshold}": []
            for threshold in query.completeness_thresholds
        }
        for interval, completeness_values in coverage_completeness_by_sample[
            sample.name
        ].items():

            for threshold, value in completeness_values.items():

                sample_stats[f"completeness_{threshold}"].append(value)

        for key, completeness_values in sample_stats.items():

            # Evaluate default level completeness row stats
            if key == f"completeness_{query.default_level}":
                nr_fully_covered_intervals = len(
                    [
                        completeness
                        for completeness in completeness_values
                        if completeness == 1
                    ]
                )
                nr_intervals = len(coverage_by_sample[sample.name])

            sample_stats[key] = round(mean(completeness_values) * 100, 2)

        sample_stats["mean_coverage"] = mean(coverage_by_sample[sample.name])

        data["completeness_rows"].append((sample.name, sample_stats))
        data["default_level_completeness_rows"].append(
            (
                sample.name,
                round((nr_fully_covered_intervals * 100) / nr_intervals, 2),
                f"{nr_intervals - nr_fully_covered_intervals}/{nr_intervals}",
            )
        )

    return data


### Functions used to create genes coverage overiew report


def get_genes_overview_incomplete_coverage_rows(
    coverage_completeness_by_sample: List[Tuple[str, Dict[str, float]]],
    genes_mapping: Dict[str, str],
    cov_level: int,
) -> List[Tuple]:
    """Creates the lines of a coverage overview report."""
    incomplete_cov_rows: List[Tuple[str, str, str, float]] = []

    for sample, interval_stats_dict in coverage_completeness_by_sample.items():
        for interval_gene_coords, completeness_stats in interval_stats_dict.items():
            if completeness_stats[cov_level] == 1:
                continue
            interva_ids = interval_gene_coords.split("_")
            ensembl_gene_id = interva_ids[0]
            hgnc_symbol: str = genes_mapping[interva_ids[0]]
            ensembl_interval_id = interva_ids[1]
            percent_completeness = round(completeness_stats[cov_level] * 100, 2)
            incomplete_cov_rows.append(
                (
                    hgnc_symbol,
                    ensembl_gene_id,
                    ensembl_interval_id,
                    sample,
                    percent_completeness,
                )
            )

    return incomplete_cov_rows


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
