from os import path
from typing import Dict, List, Optional, Tuple

import validators
from fastapi import APIRouter, Depends, HTTPException, status
from pyd4 import D4File
from sqlalchemy.orm import Session

from chanjo2.constants import WRONG_BED_FILE_MSG, WRONG_COVERAGE_FILE_MSG
from chanjo2.crud.intervals import get_genes
from chanjo2.crud.samples import get_samples_coverage_file
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_d4 import (
    get_d4_file,
    get_d4_intervals_completeness,
    get_d4_intervals_coverage,
    get_intervals_completeness,
    get_intervals_mean_coverage,
    get_sample_interval_coverage,
    get_samples_sex_metrics,
    set_interval,
)
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    FileCoverageIntervalsFileQuery,
    FileCoverageQuery,
    GeneCoverage,
    IntervalCoverage,
    IntervalType,
    SampleGeneIntervalQuery,
)

router = APIRouter()


@router.post("/coverage/d4/interval/", response_model=IntervalCoverage)
def d4_interval_coverage(query: FileCoverageQuery):
    """Return coverage on the given interval for a D4 resource located on the disk or on a remote server."""

    interval: Tuple[str, Optional[int], Optional[int]] = set_interval(
        chrom=query.chromosome, start=query.start, end=query.end
    )
    try:
        d4_file: D4File = get_d4_file(query.coverage_file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    return IntervalCoverage(
        mean_coverage=get_intervals_mean_coverage(
            d4_file=d4_file, intervals=[interval]
        )[0],
        completeness=get_intervals_completeness(
            d4_file=d4_file,
            intervals=[interval],
            completeness_thresholds=query.completeness_thresholds,
        ),
    )


@router.post("/coverage/d4/interval_file/", response_model=List[IntervalCoverage])
def d4_intervals_coverage(query: FileCoverageIntervalsFileQuery):
    """Return coverage on the given intervals for a D4 resource located on the disk or on a remote server."""

    if (
        path.exists(query.coverage_file_path) is False
        or validators.url(query.coverage_file_path) is False
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    if path.exists(query.intervals_bed_path) is False:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=WRONG_BED_FILE_MSG,
        )

    coverage_by_interval: List[int] = get_d4_intervals_coverage(
        d4_file_path=query.coverage_file_path, bed_file_path=query.intervals_bed_path
    )
    with open(query.intervals_bed_path, "r") as bed_file:
        bed_file_contents: List[List[str]] = [
            line.rstrip().split("\t")
            for line in bed_file
            if line.startswith("#") is False
        ]

    completeness_by_interval: List[Dict[int:float]] = []
    if query.completeness_thresholds:
        bed_file_regions: List[Tuple[str, int, int]] = [
            (bed_interval[0], int(bed_interval[1]), int(bed_interval[2]))
            for bed_interval in bed_file_contents
        ]
        completeness_by_interval: List[Dict[int:float]] = get_d4_intervals_completeness(
            d4_file_path=query.coverage_file_path,
            intervals=bed_file_regions,
            thresholds=query.completeness_thresholds,
        )

    interval_counter = 0
    intervals_coverage: List[IntervalCoverage] = []

    for interval in bed_file_contents:
        interval_coverage_stats = {
            "mean_coverage": coverage_by_interval[interval_counter],
            "interval_id": interval[4] if len(interval) >= 4 else None,
            "completeness": completeness_by_interval[interval_counter],
            "interval_type": IntervalType.CUSTOM,
        }
        intervals_coverage.append(IntervalCoverage(**interval_coverage_stats))
        interval_counter += 1

    return intervals_coverage


@router.get("/coverage/samples/predicted_sex", response_model=Dict)
async def get_samples_predicted_sex(coverage_file_path: str):
    try:
        d4_file: D4File = get_d4_file(coverage_file_path=coverage_file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )
    return get_samples_sex_metrics(d4_file=d4_file)


@router.post(
    "/coverage/samples/genes_coverage", response_model=Dict[str, List[GeneCoverage]]
)
async def samples_genes_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (entire gene) for a given list of samples in the database."""

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

    return {
        sample: get_sample_interval_coverage(
            db=db,
            d4_file=d4_file,
            genes=genes,
            interval_type=SQLGene,
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file in samples_d4_files
    }


@router.post(
    "/coverage/samples/transcripts_coverage",
    response_model=Dict[str, List[GeneCoverage]],
)
async def samples_transcripts_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (transcripts intervals only) for a given list of samples in the database."""

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

    return {
        sample: get_sample_interval_coverage(
            db=db,
            d4_file=d4_file,
            genes=genes,
            interval_type=SQLTranscript,
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file in samples_d4_files
    }


@router.post(
    "/coverage/samples/exons_coverage", response_model=Dict[str, List[GeneCoverage]]
)
async def samples_exons_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (exons intervals only) for a given list of samples in the database."""

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

    return {
        sample: get_sample_interval_coverage(
            db=db,
            d4_file=d4_file,
            genes=genes,
            interval_type=SQLExon,
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file in samples_d4_files
    }
