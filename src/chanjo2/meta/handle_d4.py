from decimal import Decimal
from statistics import mean
from typing import List, Optional, Tuple, Union

from numpy import ndarray, int64
from pyd4 import D4File
from sqlmodel import Session

from chanjo2.crud.intervals import get_gene_intervals
from chanjo2.models.pydantic_models import CoverageInterval
from chanjo2.models.sql_models import Exon as SQLExon
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript


def set_interval(
    chrom: str, start: Optional[int] = None, end: Optional[int] = None
) -> Tuple[str, Optional[int], Optional[int]]:
    """Create the interval tuple used by the pyd4 utility."""
    return (chrom, start, end) if start and end else chrom


def set_d4_file(coverage_file_path: str) -> D4File:
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
    """Return the mean value over a list of intervals of a D4 file."""
    return d4_file.mean(intervals)


def intervals_coverage(
    d4_file: D4File, intervals: List[Tuple[str, int, int]]
) -> List[CoverageInterval]:
    """Return coverage over a list of intervals."""
    intervals_cov: List[CoverageInterval] = []
    for interval in intervals:
        intervals_cov.append(
            CoverageInterval(
                chromosome=interval[0],
                start=interval[1],
                end=interval[2],
                mean_coverage=d4_file.mean(interval),
            )
        )
    return intervals_cov


def get_intervals_completeness(
    d4_file: D4File,
    intervals: List[Tuple[str, int, int]],
    completeness_threholds: Optional[List[int]],
) -> List[Tuple[int, Decimal]]:
    """Use NumPy to calculate the coverage completeness over a list of threshold values for a chromosomal region."""

    if completeness_threholds is None:
        return []

    completeness_values: List[Tuple[int, Decimal]] = []
    total_region_length: int = sum(
        [interval[2] - interval[1] for interval in intervals]
    )
    per_base_depth: ndarray = d4_file.load_to_np(intervals)

    for threshold in completeness_threholds:
        nr_complete_bases: int64 = 0
        for per_base_depth_region in per_base_depth:
            nr_complete_bases += (per_base_depth_region > threshold).sum()

        completeness_values.append(
            (
                threshold,
                Decimal(nr_complete_bases.item() / total_region_length)
                if nr_complete_bases
                else 0,
            )
        )

    return completeness_values


def get_genes_coverage_completeness(
    samples_d4_files: List[Tuple[str, D4File]],
    genes: List[SQLGene],
    completeness_threholds: List[Optional[int]],
) -> List[CoverageInterval]:
    """Return mean coverage and coverage completeness over a list of genes."""
    genes_cov: List[CoverageInterval] = []

    for gene in genes:
        gene_coords: List[Tuple[str, int, int]] = [
            (gene.chromosome, gene.start, gene.stop)
        ]
        samples_mean_coverage: List[Tuple[str, float]] = []
        samples_cov_completeness: List[Tuple[str, Decimal]] = []

        for sample, d4_file in samples_d4_files:
            samples_mean_coverage.append(
                (
                    sample,
                    get_intervals_mean_coverage(d4_file=d4_file, intervals=gene_coords)[
                        0
                    ],
                )
            )
            samples_cov_completeness.append(
                (
                    sample,
                    get_intervals_completeness(
                        d4_file=d4_file,
                        intervals=gene_coords,
                        completeness_threholds=completeness_threholds,
                    ),
                )
            )

        genes_cov.append(
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
    return genes_cov


def get_gene_interval_coverage_completeness(
    db: Session,
    d4_file: D4File,
    genes: List[SQLGene],
    interval_type: Union[SQLTranscript, SQLExon],
    completeness_threholds: List[Optional[int]],
) -> List[CoverageInterval]:
    """Return coverage of transcripts for a list of genes."""
    transcripts_cov: List[CoverageInterval] = []
    for gene in genes:
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
        mean_gene_cov: float = 0

        if sql_intervals:
            mean_gene_cov: float = mean(
                get_intervals_mean_coverage(d4_file=d4_file, intervals=intervals)
            )

        transcripts_cov.append(
            CoverageInterval(
                ensembl_gene_id=gene.ensembl_id,
                hgnc_id=gene.hgnc_id,
                hgnc_symbol=gene.hgnc_symbol,
                chromosome=gene.chromosome,
                start=gene.start,
                end=gene.stop,
                mean_coverage=mean_gene_cov,
                completeness=get_intervals_completeness(
                    d4_file=d4_file,
                    intervals=intervals,
                    completeness_threholds=completeness_threholds,
                ),
            )
        )
    return transcripts_cov
