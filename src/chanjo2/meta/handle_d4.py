from decimal import Decimal
from typing import List, Optional, Tuple, Union, Dict

from pyd4 import D4File
from sqlalchemy.orm import Session

from chanjo2.models.pydantic_models import (
    IntervalCoverage,
    Sex,
    IntervalType,
    GeneCoverage,
)
from chanjo2.models.sql_models import Exon as SQLExon
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript


def set_interval(
    chrom: str, start: Optional[int] = None, end: Optional[int] = None
) -> Tuple[str, Optional[int], Optional[int]]:
    """Create the interval tuple used by the pyd4 utility."""
    return (chrom, start, end) if start and end else chrom


def get_d4_file(coverage_file_path: str) -> D4File:
    """Create a D4 file from a file path/URL."""
    return D4File(coverage_file_path)


def get_intervals_coords_list(
    intervals: List[Union[SQLGene, SQLTranscript, SQLExon]]
) -> List[Tuple[str, int, int]]:
    """Return the coordinates of a list of intervals as a list of tuples."""
    interval_coords: List[Tuple[str, int, int]] = []
    for interval in intervals:
        interval_coords.append((interval.chromosome, interval.start, interval.stop))
    return interval_coords


def get_intervals_mean_coverage(
    d4_file: D4File, intervals: List[Tuple[str, int, int]]
) -> List[float]:
    """Return the mean value over a list of intervals of a d4 file."""
    return d4_file.mean(intervals)


def intervals_coverage(
    d4_file: D4File,
    intervals: List[Tuple[str, int, int]],
    completeness_thresholds: Optional[List[int]],
) -> List[IntervalCoverage]:
    """Return coverage over a list of intervals."""
    intervals_cov: List[IntervalCoverage] = []
    for interval in intervals:
        intervals_cov.append(
            IntervalCoverage(
                chromosome=interval[0],
                start=interval[1],
                end=interval[2],
                mean_coverage={"D4File": d4_file.mean(interval)},
                completeness=get_intervals_completeness(
                    d4_file=d4_file,
                    intervals=[interval],
                    completeness_thresholds=completeness_thresholds,
                ),
            )
        )
    return intervals_cov


def get_interval_completeness(
    d4_file: D4File,
    interval: Tuple[str, int, int],
    completeness_thresholds: Optional[List[int]],
) -> Dict[int, Decimal]:
    """Compute coverage completeness over threshold levels for a genomic interval."""
    if not completeness_thresholds:
        return {}

    total_region_length += interval[2] - interval[1]
    nr_complete_bases_by_threshold: List[int] = [0 for _ in completeness_thresholds]

    chrom = interval[0]
    start = interval[1]
    stop = interval[2]

    for _, _, d4_tracks_base_coverage in d4_file.enumerate_values(
        chrom, start, stop
    ):  # _ and _ -> interval chromosome and start position
        for index, threshold in enumerate(completeness_thresholds):
            if (
                d4_tracks_base_coverage[0] >= threshold
            ):  # d4_tracks_base_coverage[0] is the coverage depth for the first track in the d4 file (float)
                nr_complete_bases_by_threshold[index] += 1

    completeness_values: Dict[int, Decimal] = {}
    for index, threshold in enumerate(completeness_thresholds):
        completeness_values[threshold] = (
            Decimal(nr_complete_bases_by_threshold[index] / total_region_length)
            if nr_complete_bases_by_threshold[index]
            else 0
        )


def get_sample_gene_coverage(
    db: Session,
    d4_file: D4File,
    genes: List[SQLGene],
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    completeness_thresholds: List[Optional[int]],
) -> List[GeneCoverage]:
    genes_coverage_stats: List[GeneCoverage] = []
    for gene in genes:
        gene_coverage: GeneCoverage = GeneCoverage(
            **{
                "ensembl_gene_id": gene.ensembl_id,
                "hgnc_id": gene.hgnc_id,
                "hgnc_symbol": gene.hgnc_symbol,
                "interval_type": IntervalType.GENES,
                "inner_intervals": [],
            }
        )
        if interval_type == SQLGene:  # The interval requested is the genes itself
            gene_coordinates: Tuple[str, int, int] = (
                gene.chromosome,
                gene.start,
                gene.stop,
            )
            gene_coverage.mean_coverage = d4_file.mean(gene_coordinates)
            gene_coverage.completeness = get_interval_completeness(
                d4_file=d4_file,
                interval=gene_coordinates,
                completeness_thresholds=completeness_thresholds,
            )

        else:  # Retrieve transcripts or exons for this gene
            sql_intervals: List[Union[SQLTranscript, SQLExon]] = get_gene_intervals(
                db=db,
                build=gene.build,
                interval_type=interval_type,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                ensembl_gene_ids=[gene.ensembl_id],
                limit=None,
            )
            for interval in sql_intervals:
                interval_coordinates: Tuple[str, int, int] = (
                    interval.chromosome,
                    interval.start,
                    interval.stop,
                )
                interval_coverage = IntervalCoverage(
                    **{
                        "interval_type": interval_type,
                        "interval_id": interval.ensembl_id,
                        "mean_coverage": d4_file.mean(interval_coordinates),
                        "completeness": get_interval_completeness(
                            d4_file=d4_file,
                            interval=interval_coordinates,
                            completeness_thresholds=completeness_thresholds,
                        ),
                    }
                )
                gene_coverage.inner_intervals.append(interval_coverage)

    genes_coverage_stats.append(gene_coverage)


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


def get_samples_sex_metrics(d4_file: D4File) -> Dict:
    """Compute coverage over sex chromosomes and predicted sex."""

    sex_chroms_coverage: List[float] = get_intervals_mean_coverage(
        d4_file=d4_file, intervals=[("X"), ("Y")]
    )
    return {
        "x_coverage": round(sex_chroms_coverage[0], 1),
        "y_coverage": round(sex_chroms_coverage[1], 1),
        "predicted_sex": predict_sex(
            x_cov=sex_chroms_coverage[0], y_cov=sex_chroms_coverage[1]
        ),
    }
