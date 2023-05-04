from typing import List, Optional, Tuple

from fastapi import APIRouter, HTTPException, File, status, Depends
from pyd4 import D4File
from sqlmodel import Session

from chanjo2.constants import (
    WRONG_BED_FILE_MSG,
    WRONG_COVERAGE_FILE_MSG,
    SAMPLE_NOT_FOUND,
)
from chanjo2.crud.intervals import get_genes
from chanjo2.crud.samples import get_sample
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.meta.handle_d4 import (
    interval_coverage,
    intervals_coverage,
    set_d4_file,
    set_interval,
    genes_coverage_completeness,
    genes_transcript_coverage,
)
from chanjo2.models.pydantic_models import (
    CoverageInterval,
    SampleGeneQuery,
    SampleGeneIntervalQuery,
)
from chanjo2.models.sql_models import Gene as SQLGene

router = APIRouter()


@router.get("/coverage/d4/interval/", response_model=CoverageInterval)
def d4_interval_coverage(
    coverage_file_path: str,
    chromosome: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
):
    """Return coverage on the given interval for a D4 resource located on the disk or on a remote server."""

    interval: Tuple[str, Optional[int], Optional[int]] = set_interval(
        chrom=chromosome, start=start, end=end
    )
    try:
        d4_file: D4File = set_d4_file(coverage_file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        interval=interval,
        mean_coverage=interval_coverage(d4_file, interval),
    )


@router.post("/coverage/d4/interval_file/", response_model=List[CoverageInterval])
def d4_intervals_coverage(coverage_file_path: str, bed_file: bytes = File(...)):
    """Return coverage on the given intervals for a D4 resource located on the disk or on a remote server."""

    try:
        d4_file: D4File = set_d4_file(coverage_file_path=coverage_file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    try:
        intervals: List[Tuple[str, Optional[int], Optional[int]]] = parse_bed(
            bed_file=bed_file
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=WRONG_BED_FILE_MSG,
        )

    return intervals_coverage(d4_file=d4_file, intervals=intervals)


@router.post("/coverage/sample/genes_coverage", response_model=List[CoverageInterval])
async def sample_genes_coverage(
    query: SampleGeneQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (entire gene) for a given sample in the database."""

    sample: SQLSample = get_sample(db=db, sample_name=query.sample_name)
    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SAMPLE_NOT_FOUND,
        )
    try:
        d4_file: D4File = set_d4_file(coverage_file_path=sample.coverage_file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    genes: List[SQLGene] = get_genes(
        db=db,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        limit=None,
    )

    return genes_coverage_completeness(
        d4_file=d4_file,
        genes=genes,
        completeness_threholds=query.completeness_thresholds,
    )


@router.post(
    "/coverage/sample/transcripts_coverage", response_model=List[CoverageInterval]
)
async def sample_transcripts_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (transcripts intervals only) for a given sample in the database."""

    sample: SQLSample = get_sample(db=db, sample_name=query.sample_name)
    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SAMPLE_NOT_FOUND,
        )
    try:
        d4_file: D4File = set_d4_file(coverage_file_path=sample.coverage_file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    genes: List[SQLGene] = get_genes(
        db=db,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        limit=None,
    )

    return genes_transcript_coverage(db=db, d4_file=d4_file, genes=genes)
