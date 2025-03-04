import logging
import time
from os.path import isfile
from statistics import mean
from typing import Dict, List, Tuple

import validators
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from chanjo2.constants import WRONG_BED_FILE_MSG, WRONG_COVERAGE_FILE_MSG
from chanjo2.crud.intervals import get_genes, set_sql_intervals
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import (
    bed_file_interval_id_coords,
    sort_interval_ids_coords,
)
from chanjo2.meta.handle_completeness_stats import get_completeness_stats
from chanjo2.meta.handle_coverage_stats import (
    get_chromosomes_prefix,
    get_d4tools_chromosome_mean_coverage,
    get_d4tools_intervals_mean_coverage,
)
from chanjo2.meta.handle_d4 import get_samples_sex_metrics, set_interval_ids_coords
from chanjo2.meta.handle_report_contents import INTERVAL_TYPE_SQL_TYPE, get_mean
from chanjo2.models import SQLGene
from chanjo2.models.pydantic_models import (
    CoverageSummaryQuery,
    FileCoverageIntervalsFileQuery,
    FileCoverageQuery,
    IntervalCoverage,
    IntervalType,
    TranscriptTag,
)

router = APIRouter()
LOG = logging.getLogger(__name__)


@router.post("/coverage/d4/interval/", response_model=IntervalCoverage)
def d4_interval_coverage(query: FileCoverageQuery):
    """Return coverage on the given interval for a D4 resource located on the disk or on a remote server."""

    if (
        isfile(query.coverage_file_path) is False
        or validators.url(query.coverage_file_path) is False
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    chrom_prefix: str = get_chromosomes_prefix(query.coverage_file_path)
    chrom: str = query.chromosome.replace("chr", "")

    if None in [query.start, query.end]:  # Coverage over an entire chromosome
        return IntervalCoverage(
            mean_coverage=get_d4tools_chromosome_mean_coverage(
                d4_file_path=query.coverage_file_path,
                chromosomes=[f"{chrom_prefix}{chrom}"],
            )[0][1],
            completeness={},
            interval_id=chrom,
        )

    interval_ids_coords = [
        (
            f"{chrom}:{query.start}-{query.end}",
            (chrom, query.start, query.end),
        )
    ]

    mean_coverage: float = get_d4tools_intervals_mean_coverage(
        d4_file_path=query.coverage_file_path,
        interval_ids_coords=interval_ids_coords,
        chrom_prefix=chrom_prefix,
    )[0]

    completeness_stats = get_completeness_stats(
        d4_file_path=query.coverage_file_path,
        interval_ids_coords=[(chrom, (chrom, query.start, query.end))],
        thresholds=query.completeness_thresholds,
        chrom_prefix=chrom_prefix,
    )

    return IntervalCoverage(
        mean_coverage=mean_coverage,
        completeness=completeness_stats[chrom],
        interval_id=f"{chrom}:{query.start}-{query.end}",
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

    interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = (
        bed_file_interval_id_coords(file_path=query.intervals_bed_path)
    )

    interval_ids_coords = sort_interval_ids_coords(interval_ids_coords)

    chrom_prefix: str = get_chromosomes_prefix(query.coverage_file_path)
    intervals_coverage = get_d4tools_intervals_mean_coverage(
        d4_file_path=query.coverage_file_path,
        interval_ids_coords=interval_ids_coords,
        chrom_prefix=chrom_prefix,
    )

    intervals_completeness: Dict[str, Dict[int, float]] = get_completeness_stats(
        d4_file_path=query.coverage_file_path,
        thresholds=query.completeness_thresholds,
        interval_ids_coords=interval_ids_coords,
        chrom_prefix=chrom_prefix,
    )

    results: List[IntervalCoverage] = []
    for counter, interval_data in enumerate(interval_ids_coords):
        coords = f"{interval_data[1][0]}:{interval_data[1][1]}-{interval_data[1][2]}"
        interval_coverage = {
            "interval_type": IntervalType.CUSTOM,
            "interval_id": coords,
            "mean_coverage": intervals_coverage[counter],
            "completeness": intervals_completeness[interval_data[0]],
        }
        results.append(IntervalCoverage.model_validate(interval_coverage))

    LOG.debug(
        f"Time to compute stats on {counter+1} intervals and {len(query.completeness_thresholds)} coverage thresholds: {time.time() - start_time} seconds."
    )

    return results


@router.post("/coverage/d4/genes/summary", response_model=Dict)
def d4_genes_condensed_summary(
    query: CoverageSummaryQuery, db: Session = Depends(get_session)
):
    """Returning condensed summary containing only sample's mean coverage and completeness above a default threshold."""

    condensed_stats = {}
    genes: List[SQLGene] = get_genes(
        db=db,
        build=query.build,
        ensembl_ids=None,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=None,
        limit=None,
    )

    sql_intervals = set_sql_intervals(
        db=db,
        interval_type=INTERVAL_TYPE_SQL_TYPE[query.interval_type],
        genes=genes,
        transcript_tags=[TranscriptTag.REFSEQ_MRNA],
    )

    for sample in query.samples:
        # Make sure path to d4 files provided in the query exists
        if isfile(sample.coverage_file_path) is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=WRONG_COVERAGE_FILE_MSG,
            )

        interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = (
            set_interval_ids_coords(sql_intervals=sql_intervals)
        )

        # Sort intervals by chrom, start & stop
        interval_ids_coords = sort_interval_ids_coords(interval_ids_coords)

        chrom_prefix: str = get_chromosomes_prefix(sample.coverage_file_path)

        # Compute mean coverage over genomic intervals
        genes_mean_coverage: List[float] = get_d4tools_intervals_mean_coverage(
            d4_file_path=sample.coverage_file_path,
            interval_ids_coords=interval_ids_coords,
            chrom_prefix=chrom_prefix,
        )
        # Compute coverage completeness over genomic intervals
        genes_coverage_completeness: Dict[str, dict] = get_completeness_stats(
            d4_file_path=sample.coverage_file_path,
            thresholds=[query.coverage_threshold],
            interval_ids_coords=interval_ids_coords,
            chrom_prefix=chrom_prefix,
        )
        genes_coverage_completeness_values: List[float] = [
            value[query.coverage_threshold] * 100
            for value in genes_coverage_completeness.values()
        ]

        condensed_stats[sample.name] = {
            "mean_coverage": get_mean(float_list=genes_mean_coverage),
            "coverage_completeness_percent": (
                round(mean(genes_coverage_completeness_values), 2)
                if genes_coverage_completeness_values
                else "NA"
            ),
        }

    return condensed_stats


@router.get("/coverage/samples/predicted_sex", response_model=Dict)
async def get_samples_predicted_sex(coverage_file_path: str):
    """Return predicted sex for a sample given the coverage over its sex chromosomes."""
    if (
        isfile(coverage_file_path) is False
        or validators.url(coverage_file_path) is False
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )
    return get_samples_sex_metrics(d4_file_path=coverage_file_path)
