import logging
import time
from os.path import isfile
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
    get_d4tools_intervals_coverage,
    get_intervals_completeness,
    get_intervals_mean_coverage,
    get_sample_interval_coverage,
    get_samples_sex_metrics,
    set_interval,
)
from chanjo2.meta.handle_tasks import coverage_completeness_multitasker
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
LOG = logging.getLogger("uvicorn.access")


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

    start_time = time.time()
    if (
        isfile(query.coverage_file_path) is False
        or validators.url(query.coverage_file_path) is False
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    if isfile(query.intervals_bed_path) is False:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=WRONG_BED_FILE_MSG,
        )

    with open(query.intervals_bed_path, "r") as f:
        bed_file_contents: List[List[str]] = [
            line.rstrip().split("\t") for line in f if line.startswith("#") is False
        ]

    interval_id_coords: List[Tuple[str, tuple]] = [
        (
            interval[4] if len(interval) >= 4 else None,
            (interval[0], int(interval[1]), int(interval[2])),
        )
        for interval in bed_file_contents
    ]

    intervals_coverage: List[float] = get_d4tools_intervals_coverage(
        d4_file_path=query.coverage_file_path, bed_file_path=query.intervals_bed_path
    )
    intervals_completeness: Dict[str, Dict[int, float]] = (
        coverage_completeness_multitasker(
            d4_file_path=query.coverage_file_path,
            thresholds=query.completeness_thresholds,
            interval_ids_coords=interval_id_coords,
        )
    )

    results: List[IntervalCoverage] = []
    for counter, interval_data in enumerate(interval_id_coords):
        interval_coverage = {
            "interval_type": IntervalType.CUSTOM,
            "interval_id": interval_data[0],
            "mean_coverage": intervals_coverage[counter],
            "completeness": intervals_completeness[interval_data[0]],
        }
        results.append(IntervalCoverage(**interval_coverage))

    LOG.info(
        f"Time to compute stats on {counter+1} intervals and {len(query.completeness_thresholds)} coverage thresholds: {time.time() - start_time} seconds."
    )

    return results


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
