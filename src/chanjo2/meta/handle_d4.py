from statistics import mean
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_gene_intervals, set_sql_intervals
from chanjo2.meta.handle_bed import sort_interval_ids_coords
from chanjo2.meta.handle_completeness_stats import get_completeness_stats
from chanjo2.meta.handle_coverage_stats import (
    get_d4tools_chromosome_mean_coverage,
    get_d4tools_intervals_mean_coverage,
)
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    GeneCoverage,
    IntervalCoverage,
    IntervalType,
    Sex,
    TranscriptTag,
)


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
    interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = [
        (interval.ensembl_id, (interval.chromosome, interval.start, interval.stop))
        for interval in sql_intervals
    ]

    interval_ids_coords = sort_interval_ids_coords(interval_ids_coords)

    # Compute intervals coverage
    intervals_coverage: List[float] = get_d4tools_intervals_mean_coverage(
        d4_file_path=d4_file_path, interval_ids_coords=interval_ids_coords
    )
    completeness_row_dict: dict = {"mean_coverage": mean(intervals_coverage)}

    # Compute intervals coverage completeenss
    intervals_coverage_completeness: Dict[str, dict] = get_completeness_stats(
        d4_file_path=d4_file_path,
        thresholds=completeness_thresholds,
        interval_ids_coords=interval_ids_coords,
    )

    interval_ids = set()
    thresholds_dict = {threshold: [] for threshold in completeness_thresholds}
    incomplete_coverages_rows: List[Tuple[int, str, str, str, float]] = []
    nr_intervals_covered_under_custom_threshold: int = 0
    genes_covered_under_custom_threshold = set()

    for interval_nr, interval in enumerate(sql_intervals):
        if interval.ensembl_id in interval_ids:
            continue
        for threshold in completeness_thresholds:
            interval_coverage_at_threshold: float = intervals_coverage_completeness[
                interval.ensembl_id
            ][threshold]
            thresholds_dict[threshold].append(interval_coverage_at_threshold)

            # Collect intervals which are not completely covered at the custom threshold
            if threshold == default_threshold and interval_coverage_at_threshold < 1:
                nr_intervals_covered_under_custom_threshold += 1
                interval_ensembl_gene: str = (
                    interval.ensembl_id
                    if interval.ensembl_id.startswith("ENSG")
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
                        interval.ensembl_id,
                        sample_name,
                        round(interval_coverage_at_threshold * 100, 2),
                    )
                )

        interval_ids.add(interval.ensembl_id)

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


def get_sample_interval_coverage(
    db: Session,
    d4_file_path: str,
    genes: List[SQLGene],
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    completeness_thresholds: List[Optional[int]],
    transcript_tags: Optional[List[TranscriptTag]] = [],
) -> List[GeneCoverage]:
    """Compute stats to populate a coverage overview report for one sample."""

    if not genes:
        return []

    genes_coverage_stats: List[GeneCoverage] = []

    sql_intervals: List[Union[SQLGene, SQLTranscript, SQLExon]] = set_sql_intervals(
        db=db, interval_type=interval_type, genes=genes, transcript_tags=transcript_tags
    )
    interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = [
        (interval.ensembl_id, (interval.chromosome, interval.start, interval.stop))
        for interval in sql_intervals
    ]
    interval_ids_coords = sort_interval_ids_coords(interval_ids_coords)

    intervals_coverage_completeness: Dict[str, dict] = get_completeness_stats(
        d4_file_path=d4_file_path,
        thresholds=completeness_thresholds,
        interval_ids_coords=interval_ids_coords,
    )

    # Create GeneCoverage objects
    for gene in genes:
        gene_coverage = GeneCoverage(
            **{
                "ensembl_gene_id": gene.ensembl_id,
                "hgnc_id": gene.hgnc_id,
                "hgnc_symbol": gene.hgnc_symbol,
                "interval_type": IntervalType.GENES,
                "interval_id": gene.ensembl_id,
                "mean_coverage": 0,
                "completeness": {},
                "inner_intervals": [],
            }
        )

        if interval_type == SQLGene:  # The interval requested is the genes itself
            gene_coverage.mean_coverage = mean(
                get_d4tools_intervals_mean_coverage(
                    d4_file_path=d4_file_path,
                    interval_ids_coords=interval_ids_coords,
                )
            )
            gene_coverage.completeness = intervals_coverage_completeness.get(
                gene.ensembl_id, {}
            )

        else:  # Retrieve transcripts or exons for this gene

            gene_intervals: List[Union[SQLTranscript, SQLExon]] = get_gene_intervals(
                db=db,
                build=gene.build,
                interval_type=interval_type,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                ensembl_gene_ids=[gene.ensembl_id],
                limit=None,
                transcript_tags=transcript_tags,
            )

            inner_intervals_ensembl_ids = set()
            interval_ids_coords: List[Tuple[str, Tuple]] = []
            intervals_mean_completeness: Dict[int:List] = {
                threshold: [] for threshold in completeness_thresholds
            }

            for interval in gene_intervals:
                if interval.ensembl_id in inner_intervals_ensembl_ids:
                    continue

                interval_tuple: Tuple[str, Tuple] = (
                    interval.ensembl_id,
                    (interval.chromosome, interval.start, interval.stop),
                )
                interval_ids_coords.append(interval_tuple)

                for threshold in completeness_thresholds:
                    intervals_mean_completeness[threshold].append(
                        intervals_coverage_completeness[interval.ensembl_id][threshold]
                    )

                interval_coverage = IntervalCoverage(
                    **{
                        "interval_type": interval_type.__tablename__,
                        "interval_id": interval.ensembl_id,
                        "mean_coverage": mean(
                            get_d4tools_intervals_mean_coverage(
                                d4_file_path=d4_file_path,
                                interval_ids_coords=[interval_tuple],
                            )
                        ),
                        "completeness": intervals_coverage_completeness[
                            interval.ensembl_id
                        ],
                    }
                )

                gene_coverage.inner_intervals.append(interval_coverage)
                inner_intervals_ensembl_ids.add(interval.ensembl_id)

            gene_intervals_mean_coverage: List[float] = (
                get_d4tools_intervals_mean_coverage(
                    d4_file_path=d4_file_path, interval_ids_coords=interval_ids_coords
                )
            )
            gene_coverage.mean_coverage = (
                mean(gene_intervals_mean_coverage)
                if gene_intervals_mean_coverage
                else 0
            )

            for threshold in completeness_thresholds:
                gene_coverage.completeness[threshold] = (
                    mean(intervals_mean_completeness[threshold])
                    if intervals_mean_completeness[threshold]
                    else 0
                )

        genes_coverage_stats.append(gene_coverage)

    return genes_coverage_stats


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

    sex_chroms_coverage: List[Tuple[str, float]] = get_d4tools_chromosome_mean_coverage(
        d4_file_path=d4_file_path, chromosomes=["X", "Y"]
    )

    return {
        "x_coverage": round(sex_chroms_coverage[0][1], 1),
        "y_coverage": round(sex_chroms_coverage[1][1], 1),
        "predicted_sex": predict_sex(
            x_cov=sex_chroms_coverage[0][1], y_cov=sex_chroms_coverage[1][1]
        ),
    }
