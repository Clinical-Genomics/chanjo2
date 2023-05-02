from typing import List, Optional, Tuple

from pyd4 import D4File

from chanjo2.models.pydantic_models import CoverageInterval
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Sample as SQLSample


def set_interval(
    chrom: str, start: Optional[int] = None, end: Optional[int] = None
) -> Tuple[str, Optional[int], Optional[int]]:
    """Create the interval tuple used by the pyd4 utility."""
    return (chrom, start, end) if start and end else chrom


def set_d4_file(coverage_file_path: str) -> D4File:
    """Create a D4 file from a file path/URL."""
    return D4File(coverage_file_path)


def interval_coverage(
    d4_file: D4File, interval: Tuple[str, Optional[int], Optional[int]]
) -> float:
    """Return coverage over a single interval of a D4 file."""
    return d4_file.mean([interval])[0]


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


def genes_coverage(
    d4_file: D4File, genes: List[SQLGene], sample: SQLSample
) -> List[CoverageInterval]:
    """Return coverage over a list of genes for a sample."""
    genes_cov: List[CoverageInterval] = []
    for gene in genes:
        genes_cov.append(
            CoverageInterval(
                ensembl_gene_id=gene.ensembl_id,
                hgnc_id=gene.hgnc_id,
                hgnc_symbol=gene.hgnc_symbol,
                chromosome=gene.chromosome,
                start=gene.start,
                end=gene.stop,
                mean_coverage=d4_file.mean((gene.chromosome, gene.start, gene.stop)),
            )
        )
    return genes_cov


"""

class CoverageInterval(BaseModel):
    ensembl_gene_id: Optional[str]
    hgnc_id: Optional[str]
    hgnc_symbol: Optional[int]
    chromosome: str
    start: Optional[int]
    end: Optional[int]
    interval_id: Optional[int]
    mean_coverage: float
"""
