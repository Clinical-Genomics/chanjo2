import logging
from collections import OrderedDict
from statistics import mean
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_genes, get_hgnc_gene, set_sql_intervals
from chanjo2.meta.handle_d4 import (
    get_gene_overview_stats,
    get_report_sample_interval_coverage,
    get_samples_sex_metrics,
)
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    Builds,
    GeneReportForm,
    IntervalType,
    ReportQuery,
    ReportQuerySample,
    SampleSexRow,
    TranscriptTag,
)

LOG = logging.getLogger(__name__)
INTERVAL_TYPE_SQL_TYPE: Dict[IntervalType, Union[SQLGene, SQLTranscript, SQLExon]] = {
    IntervalType.GENES: SQLGene,
    IntervalType.TRANSCRIPTS: SQLTranscript,
    IntervalType.EXONS: SQLExon,
}

#### Functions used by all reports ####


def get_mean(float_list: List[float], round_by: int = 2) -> Union[float, str]:
    """Return the mean value from a list of floating point numbers, or a string when the value can't be converted to number."""
    if float_list:
        mean_value = round(mean(float_list), round_by)
    else:
        mean_value = "NA"

    return mean_value if str(mean_value).split(".")[0].isdigit() else str(mean_value)


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

    if any([query.ensembl_gene_ids, query.hgnc_gene_ids, query.hgnc_gene_symbols]):
        genes: List[SQLGene] = get_genes(
            db=session,
            build=query.build,
            ensembl_ids=query.ensembl_gene_ids,
            hgnc_ids=query.hgnc_gene_ids,
            hgnc_symbols=query.hgnc_gene_symbols,
            limit=None,
        )
    else:
        genes = []

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
        ensembl_id: {"hgnc_id": gene.hgnc_id, "hgnc_symbol": gene.hgnc_symbol}
        for gene in genes
        for ensembl_id in gene.ensembl_ids
    }

    sql_intervals: list = []
    if gene_ids_mapping:
        sql_intervals = set_sql_intervals(
            db=session,
            interval_type=INTERVAL_TYPE_SQL_TYPE[query.interval_type],
            genes=genes,
            transcript_tags=[
                TranscriptTag.REFSEQ_MANE_PLUS_CLINICAL,
                TranscriptTag.REFSEQ_MANE_SELECT,
                TranscriptTag.REFSEQ_MRNA,
            ],
        )

    for sample in query.samples:
        get_report_sample_interval_coverage(
            d4_file_path=sample.coverage_file_path,
            sample_name=sample.name,
            gene_ids_mapping=gene_ids_mapping,
            sql_intervals=sql_intervals,
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
    """Returns coverage stats over the intervals of one gene for one or more samples."""

    gene_stats = {
        "levels": get_ordered_levels(
            threshold_levels=form_data.completeness_thresholds
        ),
        "interval_type": form_data.interval_type.value,
        "transcript_coverage_stats": {},
    }

    set_samples_coverage_files(session=session, samples=form_data.samples)

    gene: SQLGene = get_hgnc_gene(
        build=form_data.build, hgnc_id=form_data.hgnc_gene_id, db=session
    )
    if gene is None:
        gene_stats["gene"] = {"hgnc_id": form_data.hgnc_gene_id}
        return gene_stats

    gene_stats["gene"] = gene
    transcripts_intervals = set_sql_intervals(
        db=session,
        interval_type=SQLTranscript,
        genes=[gene],
        transcript_tags=[],
    )
    exons_intervals = set_sql_intervals(db=session, interval_type=SQLExon, genes=[gene])
    sql_intervals = transcripts_intervals + exons_intervals

    samples_coverage_by_interval = get_gene_overview_stats(
        sql_intervals=sql_intervals,
        samples=form_data.samples,
        completeness_thresholds=form_data.completeness_thresholds,
    )

    for sql_interval in sql_intervals:
        interval_length: int = abs(sql_interval.stop - sql_interval.start)
        coords: str = (
            f"{sql_interval.chromosome}:{sql_interval.start}-{sql_interval.stop}"
        )

        if type(sql_interval) == SQLTranscript:
            gene_stats["transcript_coverage_stats"][sql_interval.ensembl_id] = {
                "interval_type": "transcript",
                "mane_select": sql_interval.refseq_mane_select,
                "mane_plus_clinical": sql_interval.refseq_mane_plus_clinical,
                "mrna": sql_interval.refseq_mrna,
                "stats": samples_coverage_by_interval[sql_interval.ensembl_id],
                "length": interval_length,
                "coordinates": coords,
                "exons": {},
            }
            continue

        gene_stats["transcript_coverage_stats"][sql_interval.ensembl_transcript_id][
            "exons"
        ][sql_interval.ensembl_id] = {
            "interval_type": "exon",
            "transcript_rank": int(sql_interval.rank_in_transcript),
            "stats": samples_coverage_by_interval[sql_interval.ensembl_id],
            "length": interval_length,
            "coordinates": coords,
        }

    return gene_stats


def get_mane_overview_coverage_stats(query: ReportQuery, session: Session) -> Dict:
    """Returns coverage stats over the MANE transcripts of a list of genes."""

    set_samples_coverage_files(session=session, samples=query.samples)
    genes = []
    if any([query.ensembl_gene_ids, query.hgnc_gene_ids, query.hgnc_gene_symbols]):
        genes: List[SQLGene] = get_genes(
            db=session,
            build=Builds.build_38,
            ensembl_ids=query.ensembl_gene_ids,
            hgnc_ids=query.hgnc_gene_ids,
            hgnc_symbols=query.hgnc_gene_symbols,
            limit=None,
        )

    gene_mappings = {}
    hgnc_gene_ids = []
    for gene in genes:
        hgnc_gene_ids.append(gene.hgnc_id)
        for ensembl_id in gene.ensembl_ids:
            gene_mappings[ensembl_id] = gene

    mane_stats = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "hgnc_gene_ids": hgnc_gene_ids
            or query.hgnc_gene_ids
            or query.hgnc_gene_symbols
            or query.ensembl_gene_ids,
            "interval_type": query.interval_type.value,
            "default_level": query.default_level,
            "completeness_thresholds": query.completeness_thresholds,
            "samples": [_serialize_sample(sample) for sample in query.samples],
            "panel_name": query.panel_name,
        },
        "interval_type": IntervalType.TRANSCRIPTS,
        "mane_coverage_stats": [],
    }

    sql_intervals = []
    if genes:
        sql_intervals = set_sql_intervals(
            db=session,
            interval_type=SQLTranscript,
            genes=genes,
            transcript_tags=[
                TranscriptTag.REFSEQ_MANE_SELECT,
                TranscriptTag.REFSEQ_MANE_PLUS_CLINICAL,
            ],
        )

    mane_samples_coverage_stats_by_transcript = get_gene_overview_stats(
        sql_intervals=sql_intervals,
        samples=query.samples,
        completeness_thresholds=query.completeness_thresholds,
    )

    existing_transcripts = []

    for transcript in sql_intervals:
        transcript_dict = {
            "mane_select": transcript.refseq_mane_select,
            "mane_plus_clinical": transcript.refseq_mane_plus_clinical,
        }
        if transcript_dict in existing_transcripts:
            continue

        existing_transcripts.append(transcript_dict)
        gene_symbol: str = gene_mappings[transcript.ensembl_gene_id].hgnc_symbol
        data_dict: dict = {
            "gene": {
                "hgnc_id": gene_mappings[transcript.ensembl_gene_id].hgnc_id,
                "ensembl_ids": gene_mappings[transcript.ensembl_gene_id].ensembl_ids,
            },
            "transcript": transcript_dict,
            "stats": mane_samples_coverage_stats_by_transcript[transcript.ensembl_id],
        }
        mane_stats["mane_coverage_stats"].append((gene_symbol, data_dict))

    return mane_stats
