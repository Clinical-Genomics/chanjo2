import logging
import tempfile
from statistics import mean
from typing import Dict, List, Optional, Tuple, Union

from chanjo2.meta.handle_bed import sort_interval_ids_coords
from chanjo2.meta.handle_completeness_stats import (
    get_completeness_stats,
    get_d4tools_intervals_completeness,
)
from chanjo2.meta.handle_coverage_stats import (
    get_chromosomes_prefix,
    get_d4tools_chromosome_mean_coverage,
    get_d4tools_intervals_coverage,
    get_d4tools_intervals_mean_coverage,
)
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import ReportQuerySample, Sex

LOG = logging.getLogger(__name__)


def set_interval_ids_coords(
    sql_intervals: List[Union[SQLGene, SQLTranscript, SQLExon]],
) -> List[Tuple[str, Tuple[str, int, int]]]:
    """Returns tuples with an ensembl_id and coordinates from a list of SQL intervals."""

    if not sql_intervals:
        return []
    if isinstance(sql_intervals[0], SQLGene):
        return [
            (ensembl_id, (interval.chromosome, interval.start, interval.stop))
            for interval in sql_intervals
            for ensembl_id in interval.ensembl_ids
        ]
    else:
        return [
            (interval.ensembl_id, (interval.chromosome, interval.start, interval.stop))
            for interval in sql_intervals
        ]


def get_report_sample_interval_coverage(
    d4_file_path: str,
    sample_name: str,
    gene_ids_mapping: Dict[str, dict],
    sql_intervals: List[Union[SQLGene, SQLTranscript, SQLExon]],
    completeness_thresholds: List[Optional[int]],
    default_threshold: int,
    report_data: dict,
) -> None:
    """Compute stats to populate a coverage report for one sample."""

    # Compute intervals coverage completeness
    interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = (
        set_interval_ids_coords(sql_intervals=sql_intervals)
    )
    interval_ids_coords = sort_interval_ids_coords(interval_ids_coords)

    chrom_prefix: str = get_chromosomes_prefix(d4_file_path)

    # Compute intervals coverage
    intervals_coverage: List[float] = get_d4tools_intervals_mean_coverage(
        d4_file_path=d4_file_path,
        interval_ids_coords=interval_ids_coords,
        chrom_prefix=chrom_prefix,
    )
    completeness_row_dict: dict = {"mean_coverage": mean(intervals_coverage)}

    # Compute intervals coverage completeenss
    intervals_coverage_completeness: Dict[str, dict] = get_completeness_stats(
        d4_file_path=d4_file_path,
        thresholds=completeness_thresholds,
        interval_ids_coords=interval_ids_coords,
        chrom_prefix=chrom_prefix,
    )

    interval_ids = set()
    thresholds_dict = {threshold: [] for threshold in completeness_thresholds}
    incomplete_coverages_rows: List[Tuple[int, str, str, str, float]] = []
    nr_intervals_covered_under_custom_threshold: int = 0
    genes_covered_under_custom_threshold = set()

    for interval in sql_intervals:

        if hasattr(interval, "ensembl_ids"):
            ensembl_ids = interval.ensembl_ids
        else:
            ensembl_ids = [interval.ensembl_id]

        for ensembl_id in ensembl_ids:

            if ensembl_id in interval_ids:
                continue
            for threshold in completeness_thresholds:
                interval_coverage_at_threshold: float = intervals_coverage_completeness[
                    ensembl_id
                ][threshold]
                thresholds_dict[threshold].append(interval_coverage_at_threshold)

                # Collect intervals which are not completely covered at the custom threshold
                if (
                    threshold == default_threshold
                    and interval_coverage_at_threshold < 1
                ):
                    nr_intervals_covered_under_custom_threshold += 1
                    interval_ensembl_gene: str = (
                        ensembl_id
                        if ensembl_id.startswith("ENSG")
                        else interval.ensembl_gene_id
                    )
                    interval_hgnc_id: int = gene_ids_mapping[interval_ensembl_gene][
                        "hgnc_id"
                    ]
                    interval_hgnc_symbol: str = gene_ids_mapping[interval_ensembl_gene][
                        "hgnc_symbol"
                    ]
                    genes_covered_under_custom_threshold.add(interval_hgnc_symbol)
                    incomplete_coverages_rows.append(
                        (
                            interval_hgnc_symbol,
                            interval_hgnc_id,
                            ensembl_id,
                            (
                                {
                                    "mane_select": interval.refseq_mane_select,
                                    "mane_plus_clinical": interval.refseq_mane_plus_clinical,
                                    "mrna": interval.refseq_mrna,
                                }
                                if isinstance(interval, SQLTranscript)
                                else {}
                            ),
                            sample_name,
                            round(interval_coverage_at_threshold * 100, 2),
                        )
                    )

            interval_ids.add(ensembl_id)

    for threshold in completeness_thresholds:
        if thresholds_dict[threshold]:
            completeness_row_dict[f"completeness_{threshold}"] = round(
                mean(thresholds_dict[threshold]) * 100, 2
            )

    report_data["completeness_rows"].append((sample_name, completeness_row_dict))
    report_data["incomplete_coverage_rows"] += incomplete_coverages_rows
    if interval_ids_coords:
        fully_covered_intervals_percent = round(
            100
            * (len(interval_ids) - nr_intervals_covered_under_custom_threshold)
            / len(interval_ids),
            2,
        )
        report_data["default_level_completeness_rows"].append(
            (
                sample_name,
                fully_covered_intervals_percent,
                f"{nr_intervals_covered_under_custom_threshold}/{len(interval_ids)}",
                genes_covered_under_custom_threshold,
            )
        )


def predict_sex(x_cov: float, y_cov: float) -> str:
    """Return predict sex based on sex chromosomes coverage - this code is taken from the old chanjo."""
    if y_cov == 0:
        return Sex.FEMALE.value
    else:
        ratio: float = x_cov / y_cov
        if x_cov == 0 or (ratio > 12 and ratio < 100):
            return Sex.UNKNOWN.value
        elif ratio <= 12:
            # this is the entire prediction, it's usually very obvious
            return Sex.MALE.value
        else:
            # the few reads mapping to the Y chromosomes are artifacts
            return Sex.FEMALE.value


def get_samples_sex_metrics(d4_file_path: str) -> Dict:
    """Compute coverage over sex chromosomes and predicted sex."""

    chrom_prefix: str = get_chromosomes_prefix(d4_file_path)

    sex_chroms_coverage: List[Tuple[str, float]] = get_d4tools_chromosome_mean_coverage(
        d4_file_path=d4_file_path, chromosomes=[f"{chrom_prefix}X", f"{chrom_prefix}Y"]
    )

    return {
        "x_coverage": round(sex_chroms_coverage[0][1], 1),
        "y_coverage": round(sex_chroms_coverage[1][1], 1),
        "predicted_sex": predict_sex(
            x_cov=sex_chroms_coverage[0][1], y_cov=sex_chroms_coverage[1][1]
        ),
    }


def get_gene_overview_stats(
    sql_intervals: List[SQLTranscript],
    samples: List[ReportQuerySample],
    completeness_thresholds: List[int],
) -> Dict[str, list]:
    """Returns stats to be included in the gene overview page."""
    interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = (
        set_interval_ids_coords(sql_intervals=sql_intervals)
    )
    interval_ids_coords = tuple(
        sort_interval_ids_coords(set(interval_ids_coords))
    )  # removes duplicates and orders intervals by chromosome, start and stop
    transcripts_stats = {interval_id: [] for interval_id, _ in interval_ids_coords}

    chrom_prefix: str = get_chromosomes_prefix(
        samples[0].coverage_file_path
    )  # Assume they are all using the same reference

    # create a temp bed file containing transcripts coordinates
    bed_lines = [
        f"{chrom_prefix}{coords[0]}\t{coords[1]}\t{coords[2]}"
        for _, coords in interval_ids_coords
    ]
    temp_bed_file = tempfile.NamedTemporaryFile()
    with open(temp_bed_file.name, "w") as intervals_bed:
        intervals_bed.write("\n".join(bed_lines))
        intervals_bed.flush()

    for sample in samples:
        transcripts_coverage = get_d4tools_intervals_coverage(
            d4_file_path=sample.coverage_file_path, bed_file_path=temp_bed_file.name
        )
        transcripts_completeness = get_d4tools_intervals_completeness(
            d4_file_path=sample.coverage_file_path,
            bed_file_path=temp_bed_file.name,
            completeness_thresholds=completeness_thresholds,
        )
        for idx, transcripts_coords in enumerate(interval_ids_coords):
            append_tuple = (
                sample.name,
                transcripts_coverage[idx],
                transcripts_completeness[idx],
            )
            transcripts_stats[transcripts_coords[0]].append(append_tuple)

    return transcripts_stats
