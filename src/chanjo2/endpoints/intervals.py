from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from chanjo2.constants import MULTIPLE_PARAMS_NOT_SUPPORTED_MSG
from chanjo2.crud.intervals import get_gene_intervals, get_genes
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_load_intervals import update_interval_table
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    Builds,
    ExonBase,
    GeneBase,
    GeneIntervalQuery,
    GeneQuery,
    IntervalType,
    TranscriptBase,
)

router = APIRouter()


def count_nr_filters(filters: List[str]) -> int:
    """Count the items in a query list that aren't null."""
    return sum(filter is not None for filter in filters)


@router.post("/intervals/load/genes/{build}")
async def load_genes(
    background_tasks: BackgroundTasks,
    build: Builds,
    file_path: str,
    session: Session = Depends(get_session),
) -> dict:
    """Load genes in the given genome build."""

    print(f"Loading {build} genes.")
    background_tasks.add_task(
        update_interval_table, IntervalType.GENES, build, file_path, session
    )
    return {
        "message": "Genes will be updated in background. Please check their availability in a few minutes."
    }


@router.post("/intervals/genes", response_model=List[GeneBase])
async def genes(query: GeneQuery, session: Session = Depends(get_session)):
    """Return genes according to query parameters."""
    nr_filters = count_nr_filters(
        filters=[query.ensembl_ids, query.hgnc_ids, query.hgnc_symbols]
    )
    if nr_filters > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
        )

    return get_genes(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        limit=query.limit if nr_filters == 0 else None,
    )


@router.post("/intervals/load/transcripts/{build}")
async def load_transcripts(
    background_tasks: BackgroundTasks,
    build: Builds,
    file_path: str,
    session: Session = Depends(get_session),
) -> dict:
    """Load transcripts in the given genome build."""

    background_tasks.add_task(
        update_interval_table, IntervalType.TRANSCRIPTS, build, file_path, session
    )
    return {
        "message": "Transcripts will be updated in background. Please check their availability in a few minutes."
    }


@router.post("/intervals/transcripts", response_model=List[TranscriptBase])
async def transcripts(
    query: GeneIntervalQuery, session: Session = Depends(get_session)
):
    """Return transcripts according to query parameters."""
    nr_filters = count_nr_filters(
        filters=[
            query.ensembl_ids,
            query.hgnc_ids,
            query.hgnc_symbols,
            query.ensembl_gene_ids,
        ]
    )
    if nr_filters > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
        )
    return get_gene_intervals(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        ensembl_gene_ids=query.ensembl_gene_ids,
        limit=query.limit if nr_filters == 0 else None,
        interval_type=SQLTranscript,
    )


@router.post("/intervals/load/exons/{build}")
async def load_exons(
    background_tasks: BackgroundTasks,
    build: Builds,
    file_path: str,
    session: Session = Depends(get_session),
) -> dict:
    """Load exons in the given genome build."""

    background_tasks.add_task(
        update_interval_table, IntervalType.EXONS, build, file_path, session
    )
    return {
        "message": "Exons will be updated in background. Please check their availability in a few minutes."
    }


@router.post("/intervals/exons", response_model=List[ExonBase])
async def exons(query: GeneIntervalQuery, session: Session = Depends(get_session)):
    """Return exons in the given genome build."""
    nr_filters = count_nr_filters(
        filters=[
            query.ensembl_ids,
            query.hgnc_ids,
            query.hgnc_symbols,
            query.ensembl_gene_ids,
        ]
    )
    if nr_filters > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
        )

    return get_gene_intervals(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        ensembl_gene_ids=query.ensembl_gene_ids,
        limit=query.limit if nr_filters == 0 else None,
        interval_type=SQLExon,
    )
