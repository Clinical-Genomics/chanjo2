from decimal import Decimal
from statistics import mean
from typing import List, Optional, Tuple, Union, Dict

from pyd4 import D4File
from sqlmodel import Session

from chanjo2.crud.intervals import get_gene_intervals
from chanjo2.models.pydantic_models import CoverageInterval, Sex
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
) -> List[CoverageInterval]:
    """Return coverage over a list of intervals."""
    intervals_cov: List[CoverageInterval] = []
    for interval in intervals:
        intervals_cov.append(
            CoverageInterval(
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


def get_intervals_completeness(
    d4_file: D4File,
    intervals: List[Tuple[str, int, int]],
    completeness_thresholds: Optional[List[int]],
) -> List[Tuple[int, Decimal]]:
    """Compute coverage completeness over threshold values for a list of intervals."""

    if not completeness_thresholds:
        return []

    total_region_length: int = 0
    nr_complete_bases_by_threshold: List[int] = [0 for _ in completeness_thresholds]

    for interval in intervals:
        chrom: str = interval[0]
        start: int = interval[1]
        stop: int = interval[2]

        total_region_length += stop - start

        for _, _, d4_tracks_base_coverage in d4_file.enumerate_values(
            chrom, start, stop
        ):  # _ and _ -> interval chromosome and start position
            for index, threshold in enumerate(completeness_thresholds):
                if (
                    d4_tracks_base_coverage[0] >= threshold
                ):  # d4_tracks_base_coverage[0] is the coverage depth for the first track in the d4 file (float)
                    nr_complete_bases_by_threshold[index] += 1

    completeness_values: List[Tuple[int, Decimal]] = []

    for index, threshold in enumerate(completeness_thresholds):
        completeness_values.append(
            (
                threshold,
                Decimal(nr_complete_bases_by_threshold[index] / total_region_length)
                if nr_complete_bases_by_threshold[index]
                else 0,
            )
        )
    return completeness_values


def get_gene_interval_coverage_completeness(
    db: Session,
    samples_d4_files: List[Tuple[str, D4File]],
    genes: List[SQLGene],
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    completeness_thresholds: List[Optional[int]],
) -> List[CoverageInterval]:
    """Return coverage and completeness over a list of genes/transcripts/exons."""
    intervals_cov: List[CoverageInterval] = []
    for gene in genes:
        if interval_type == SQLGene:  # The interval requested is the genes itself
            sql_intervals: List[SQLGene] = [gene]
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

        intervals: List[Tuple[str, int, int]] = get_intervals_coords_list(
            intervals=sql_intervals
        )

        samples_mean_coverage: dict = {}
        samples_cov_completeness: dict = {}

        if intervals:
            for sample, d4_file in samples_d4_files:
                samples_mean_coverage[sample] = mean(
                    get_intervals_mean_coverage(d4_file=d4_file, intervals=intervals)
                )
                samples_cov_completeness[sample] = get_intervals_completeness(
                    d4_file=d4_file,
                    intervals=intervals,
                    completeness_thresholds=completeness_thresholds,
                )
        intervals_cov.append(
            CoverageInterval(
                ensembl_gene_id=gene.ensembl_id,
                hgnc_id=gene.hgnc_id,
                hgnc_symbol=gene.hgnc_symbol,
                chromosome=gene.chromosome,
                start=gene.start,
                end=gene.stop,
                mean_coverage=samples_mean_coverage,
                completeness=samples_cov_completeness,
            )
        )
    return intervals_cov


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
