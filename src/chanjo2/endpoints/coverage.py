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
from chanjo2.crud.samples import get_samples_coverage_file
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import bed_file_interval_id_coords
from chanjo2.meta.handle_completeness_tasks import (
    coverage_completeness_multitasker,
    get_d4tools_coverage_completeness,
)
from chanjo2.meta.handle_d4 import (
    get_d4tools_chromosome_mean_coverage,
    get_d4tools_intervals_coverage,
    get_d4tools_intervals_mean_coverage,
    get_sample_interval_coverage,
    get_samples_sex_metrics,
)
from chanjo2.meta.handle_report_contents import INTERVAL_TYPE_SQL_TYPE
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    CoverageSummaryQuery,
    FileCoverageIntervalsFileQuery,
    FileCoverageQuery,
    GeneCoverage,
    IntervalCoverage,
    IntervalType,
    SampleGeneIntervalQuery,
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

    interval: str = query.chromosome
    if None in [query.start, query.end]:  # Coverage over an entire chromosome
        return IntervalCoverage(
            mean_coverage=get_d4tools_chromosome_mean_coverage(
                d4_file_path=query.coverage_file_path, chromosomes=[query.chromosome]
            )[0][1],
            completeness={},
            interval_id=interval,
        )

    interval += f"\t{query.start}\t{query.end}"
    completeness_dict = {}

    mean_coverage: float = get_d4tools_intervals_mean_coverage(
        d4_file_path=query.coverage_file_path, intervals=[interval]
    )[0]
    get_d4tools_coverage_completeness(
        d4_file_path=query.coverage_file_path,
        interval_ids_coords=[(interval, (query.chromosome, query.start, query.end))],
        thresholds=query.completeness_thresholds,
        return_dict=completeness_dict,
    )

    return IntervalCoverage(
        mean_coverage=mean_coverage,
        completeness=completeness_dict.get(interval),
        interval_id=f"{query.chromosome}:{query.start}-{query.end}",
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

    interval_id_coords: List[Tuple[str, Tuple[str, int, int]]] = (
        bed_file_interval_id_coords(file_path=query.intervals_bed_path)
    )

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
        # Compute mean coverage over genomic intervals
        coverage_intervals: List[str] = [
            f"{interval.chromosome}\t{interval.start}\t{interval.stop}"
            for interval in sql_intervals
        ]
        genes_mean_coverage: List[float] = get_d4tools_intervals_mean_coverage(
            d4_file_path=sample.coverage_file_path, intervals=coverage_intervals
        )
        # Compute coverage completeness over genomic intervals
        interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = [
            (interval.ensembl_id, (interval.chromosome, interval.start, interval.stop))
            for interval in sql_intervals
        ]
        genes_coverage_completeness: Dict[str, dict] = (
            coverage_completeness_multitasker(
                d4_file_path=sample.coverage_file_path,
                thresholds=[query.coverage_threshold],
                interval_ids_coords=interval_ids_coords,
            )
        )
        genes_coverage_completeness_values: List[float] = [
            value[query.coverage_threshold] * 100
            for value in genes_coverage_completeness.values()
        ]
        condensed_stats[sample.name] = {
            "mean_coverage": (
                round(mean(genes_mean_coverage), 2) if genes_mean_coverage else "NA"
            ),
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


@router.post(
    "/coverage/samples/genes_coverage", response_model=Dict[str, List[GeneCoverage]]
)
async def samples_genes_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (entire gene) for a given list of samples in the database."""

    samples_d4_files: Tuple[str, str] = get_samples_coverage_file(
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
            d4_file_path=d4_file_path,
            genes=genes,
            interval_type=SQLGene,
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file_path in samples_d4_files
    }


@router.post(
    "/coverage/samples/transcripts_coverage",
    response_model=Dict[str, List[GeneCoverage]],
)
async def samples_transcripts_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (transcripts intervals only) for a given list of samples in the database."""

    samples_d4_files: Tuple[str, str] = get_samples_coverage_file(
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
            d4_file_path=d4_file_path,
            genes=genes,
            interval_type=SQLTranscript,
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file_path in samples_d4_files
    }


@router.post(
    "/coverage/samples/exons_coverage", response_model=Dict[str, List[GeneCoverage]]
)
async def samples_exons_coverage(
    query: SampleGeneIntervalQuery, db: Session = Depends(get_session)
):
    """Returns coverage over a list of genes (exons intervals only) for a given list of samples in the database."""

    samples_d4_files: Tuple[str, str] = get_samples_coverage_file(
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
            d4_file_path=d4_file_path,
            genes=genes,
            interval_type=SQLExon,
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file_path in samples_d4_files
    }
