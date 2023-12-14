import logging
from statistics import mean
from typing import Dict, List, Optional, Tuple, Union

from pyd4 import D4File
from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_gene_intervals
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    GeneCoverage,
    IntervalCoverage,
    IntervalType,
    Sex,
    TranscriptTag,
)

LOG = logging.getLogger("uvicorn.access")


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
                mean_coverage=d4_file.mean(interval),
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
) -> Optional[Dict[int, float]]:
    """Compute coverage completeness over threshold values for a list of intervals."""

    if not completeness_thresholds:
        return None

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

    completeness_values: Dict[int, float] = {}

    for index, threshold in enumerate(completeness_thresholds):
        completeness_values[threshold] = (
            float(nr_complete_bases_by_threshold[index] / total_region_length)
            if nr_complete_bases_by_threshold[index]
            else 0
        )

    return completeness_values


def get_sample_interval_coverage(
    db: Session,
    d4_file: D4File,
    genes: List[SQLGene],
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    completeness_thresholds: List[Optional[int]],
    transcript_tags: Optional[List[TranscriptTag]] = [],
) -> List[GeneCoverage]:
    genes_coverage_stats: List[GeneCoverage] = []
    for gene in genes:
        gene_coverage = GeneCoverage(
            **{
                "ensembl_gene_id": gene.ensembl_id,
                "hgnc_id": gene.hgnc_id,
                "hgnc_symbol": gene.hgnc_symbol,
                "interval_type": IntervalType.GENES,
                "mean_coverage": 0,
                "completeness": {},
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
            gene_coverage.completeness = get_intervals_completeness(
                d4_file=d4_file,
                intervals=[gene_coordinates],
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
                transcript_tags=transcript_tags,
            )

            intervals_coords: List[Tuple[str, int, int]] = get_intervals_coords_list(
                intervals=sql_intervals
            )

            intervals_mean_covs: List[float] = get_intervals_mean_coverage(
                d4_file=d4_file, intervals=intervals_coords
            )
            gene_coverage.mean_coverage = (
                mean(intervals_mean_covs) if intervals_mean_covs else 0
            )

            gene_coverage.completeness = get_intervals_completeness(
                d4_file=d4_file,
                intervals=intervals_coords,
                completeness_thresholds=completeness_thresholds,
            )

            inner_intervals_ensembl_ids = set()

            for interval in sql_intervals:
                if interval.ensembl_id in inner_intervals_ensembl_ids:
                    continue

                interval_coordinates: Tuple[str, int, int] = (
                    interval.chromosome,
                    interval.start,
                    interval.stop,
                )

                interval_coverage = IntervalCoverage(
                    **{
                        "interval_type": interval_type.__tablename__,
                        "interval_id": _get_interval_id(sql_interval=interval),
                        "mean_coverage": d4_file.mean(interval_coordinates),
                        "completeness": get_intervals_completeness(
                            d4_file=d4_file,
                            intervals=[interval_coordinates],
                            completeness_thresholds=completeness_thresholds,
                        ),
                    }
                )

                gene_coverage.inner_intervals.append(interval_coverage)

                inner_intervals_ensembl_ids.add(interval.ensembl_id)

        genes_coverage_stats.append(gene_coverage)

    return genes_coverage_stats


def _get_interval_id(sql_interval: Union[SQLTranscript, SQLExon]) -> str:
    """Returns an Ensembl ID for an exon or several joined IDs (Ensembl, Mane or RefSeq) for a transcript."""

    interval_ids = []
    interval_as_dict = sql_interval.__dict__
    for field in [member.value for member in TranscriptTag]:
        transcript_tag = interval_as_dict.get(field)
        if transcript_tag:
            interval_ids.append(transcript_tag)

    return ", ".join(interval_ids) or sql_interval.ensembl_id


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
