from typing import List, Optional, Tuple, Union

from fastapi import APIRouter, HTTPException, File, status, Depends
from fastapi.responses import JSONResponse
from pyd4 import D4File
from sqlmodel import Session

from chanjo2.constants import (
    WRONG_BED_FILE_MSG,
    WRONG_COVERAGE_FILE_MSG,
    SAMPLE_NOT_FOUND,
)
from chanjo2.crud.intervals import get_genes
from chanjo2.crud.samples import get_samples_by_name, get_case_samples
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.meta.handle_d4 import (
    intervals_coverage,
    get_intervals_mean_coverage,
    get_d4_file,
    set_interval,
    get_genes_coverage_completeness,
    get_gene_interval_coverage_completeness,
)
from chanjo2.models.pydantic_models import (
    CoverageInterval,
    SampleGeneIntervalQuery,
)
from chanjo2.models.sql_models import Exon as SQLExon
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript

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
        d4_file: D4File = get_d4_file(coverage_file_path)
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
        mean_coverage=[
            (
                "D4File",
                get_intervals_mean_coverage(d4_file=d4_file, intervals=[interval])[0],
            )
        ],
    )


@router.post("/coverage/d4/interval_file/", response_model=List[CoverageInterval])
def d4_intervals_coverage(coverage_file_path: str, bed_file: bytes = File(...)):
    """Return coverage on the given intervals for a D4 resource located on the disk or on a remote server."""

    try:
        d4_file: D4File = get_d4_file(coverage_file_path=coverage_file_path)
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


def get_samples_coverage_file(
    db: Session, samples: Optional[List[str]], case: Optional[str]
) -> Union[List[Tuple[str, D4File]], JSONResponse]:
    """Return a list of sample names with relative D4 coverage files."""

    samples_d4_files: List[Tuple[str, D4File]] = []
    sql_samples: List[SQLSample] = (
        get_samples_by_name(db=db, sample_names=samples)
        if samples
        else get_case_samples(db=db, case_name=case)
    )

    if samples and len(sql_samples) < len(samples) or not sql_samples:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=SAMPLE_NOT_FOUND,
        )
    for sqlsample in sql_samples:
        try:
            d4_file: D4File = get_d4_file(
                coverage_file_path=sqlsample.coverage_file_path
            )
            samples_d4_files.append((sqlsample.name, d4_file))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=WRONG_COVERAGE_FILE_MSG,
            )

    return samples_d4_files


@router.post("/coverage/samples/genes_coverage", response_model=List[CoverageInterval])
async def samples_genes_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (entire gene) for a given sample in the database."""

    samples_d4_files: Tuple[str, D4File] = get_samples_coverage_file(
        db=db, samples=query.samples, case=query.case
    )

    genes: List[SQLGene] = get_genes(
        db=db,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )

    return get_genes_coverage_completeness(
        samples_d4_files=samples_d4_files,
        genes=genes,
        completeness_threholds=query.completeness_thresholds,
    )


@router.post(
    "/coverage/samples/transcripts_coverage", response_model=List[CoverageInterval]
)
async def samples_transcripts_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (transcripts intervals only) for a given sample in the database."""

    samples_d4_files: Tuple[str, D4File] = get_samples_coverage_file(
        db=db, samples=query.samples, case=query.case
    )

    genes: List[SQLGene] = get_genes(
        db=db,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )

    return get_gene_interval_coverage_completeness(
        db=db,
        samples_d4_files=samples_d4_files,
        genes=genes,
        interval_type=SQLTranscript,
        completeness_threholds=query.completeness_thresholds,
    )


@router.post("/coverage/samples/exons_coverage", response_model=List[CoverageInterval])
async def samples_exons_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (exons intervals only) for a given sample in the database."""

    samples_d4_files: Tuple[str, D4File] = get_samples_coverage_file(
        db=db, samples=query.samples, case=query.case
    )

    genes: List[SQLGene] = get_genes(
        db=db,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )

    return get_gene_interval_coverage_completeness(
        db=db,
        samples_d4_files=samples_d4_files,
        genes=genes,
        interval_type=SQLExon,
        completeness_threholds=query.completeness_thresholds,
    )
